from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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

redis_client = redis.from_url(REDIS_URL)


@app.post("/call/initiate")
async def initiate_call(request: Request):
    """Инициировать звонок: вызывает провайдера, сохраняет в БД, уведомляет logging."""
    data = await request.json()
    user_id = data.get("user_id")

    # Вызов провайдера
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PROVIDER_URL}/call",
                json={"user_id": user_id},
                timeout=10.0,
            )
            call_status = response.json().get("status", "unknown")
        except Exception:
            call_status = "failed"

    # Problem 2: Сохраняем звонок в PostgreSQL
    db = SessionLocal()
    try:
        call = Call(user_id=user_id, status=call_status, created_at=datetime.utcnow())
        db.add(call)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    finally:
        db.close()

    # Инвалидируем кэш для этого пользователя
    cache_key = f"history:{user_id}"
    try:
        redis_client.delete(cache_key)
    except Exception:
        pass

    # Problem 6: Observer — уведомление в Logging Service
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{LOGGING_SERVICE_URL}/notification",
                json={"event": "call", "status": call_status, "user_id": user_id},
                timeout=5.0,
            )
            # Также отправляем лог
            await client.post(
                f"{LOGGING_SERVICE_URL}/log",
                json={"event": "call", "status": call_status, "user_id": user_id},
                timeout=5.0,
            )
    except Exception:
        pass

    return {"status": call_status, "user_id": user_id}


@app.get("/history/{user_id}")
async def get_history(user_id: int):
    """Получить историю звонков пользователя (с Redis-кэшем)."""
    # Problem 4: Правильный ключ кэша с user_id
    cache_key = f"history:{user_id}"

    # Пытаемся получить из кэша
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass  # Если Redis недоступен — идём в БД

    # Получаем из БД
    db = SessionLocal()
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()

    result = [
        {"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()}
        for c in calls
    ]

    # Сохраняем в кэш
    try:
        redis_client.setex(cache_key, 60, json.dumps(result))
    except Exception:
        pass

    return result


@app.post("/call/callback")
async def call_callback(request: Request):
    """Callback от провайдера (опционально, для асинхронной схемы)."""
    data = await request.json()
    return {"status": "received", "data": data}
