from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import redis
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://call_provider:8003")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# Redis клиент
redis_client = redis.from_url(REDIS_URL)


# Pydantic-модель для корректного парсинга JSON из тела запроса
class CallInitiateRequest(BaseModel):
    user_id: int


# Инициировать звонок
@app.post("/call/initiate")
async def initiate_call(request: CallInitiateRequest):
    user_id = request.user_id

    # 1. Обращаемся к Call Provider
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PROVIDER_URL}/call",
                json={"user_id": user_id},
                timeout=5.0
            )
            call_status = response.json().get("status", "unknown")
        except Exception as e:
            print(f"Call Provider error: {e}")
            call_status = "failed"

    # 2. Сохраняем звонок в PostgreSQL
    db = SessionLocal()
    try:
        new_call = Call(user_id=user_id, status=call_status)
        db.add(new_call)
        db.commit()
        db.refresh(new_call)

        # 3. Отправляем событие в Logging Service (обычный лог)
        try:
            async with httpx.AsyncClient() as log_client:
                await log_client.post(
                    f"{LOGGING_SERVICE_URL}/log",
                    json={
                        "event": "call_initiated",
                        "user_id": user_id,
                        "status": call_status,
                        "call_id": new_call.id
                    },
                    timeout=5.0
                )
        except Exception as e:
            print(f"Failed to send log event to Logging Service: {e}")

        # ✅ 4. НОВОЕ: Отправка уведомления (Observer pattern)
        # Если звонок успешен (статус "answered"), отправляем уведомление на /notification
        if call_status == "answered":
            try:
                async with httpx.AsyncClient() as notif_client:
                    await notif_client.post(
                        f"{LOGGING_SERVICE_URL}/notification",
                        json={
                            "event": "call",
                            "status": "answered",
                            "user_id": user_id
                        },
                        timeout=5.0
                    )
            except Exception as e:
                print(f"Failed to send notification to Logging Service: {e}")

        # 5. Инвалидируем кэш Redis
        cache_key = f"history:{user_id}"
        redis_client.delete(cache_key)

        return {"status": call_status, "user_id": user_id}
    finally:
        db.close()


# Получить историю звонков пользователя
@app.get("/history/{user_id}")
async def get_history(user_id: int):
    # ИСПРАВЛЕНО: ключ Redis теперь содержит user_id
    cache_key = f"history:{user_id}"

    # Пытаемся получить из кэша
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Получаем из БД
    db = SessionLocal()
    try:
        calls = db.query(Call).filter(Call.user_id == user_id).all()
        result = [
            {
                "id": c.id,
                "user_id": c.user_id,
                "status": c.status,
                "created_at": c.created_at.isoformat()
            }
            for c in calls
        ]
    finally:
        db.close()

    # Сохраняем в кэш на 60 секунд
    redis_client.setex(cache_key, 60, json.dumps(result))

    return result