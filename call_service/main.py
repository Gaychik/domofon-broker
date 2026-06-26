from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Проблема: Redis подключен, но не используется правильно
redis_client = redis.from_url(REDIS_URL)


class CallRequest(BaseModel):
    user_id: int


class CallCallback(BaseModel):
    user_id: int
    status: str


#Инициировать звонок
# ПРОБЛЕМА №2: Не сохраняет звонок в PostgreSQL
# ПРОБЛЕМА №6: Не отправляет уведомление о звонке
@app.post("/call/initiate")
async def initiate_call(call_data: CallRequest):
   
    async with httpx.AsyncClient() as client:
        try:
            # Проблема: PROVIDER_URL может быть недоступен из-за неправильного имени сервиса
            response = await client.post(f"{PROVIDER_URL}/call", json={"user_id": call_data.user_id})
            call_status = response.json().get("status", "unknown")
        except:
            call_status = "failed"
    
    # ИСПРАВЛЕНИЕ #2: Сохраняем звонок в PostgreSQL
    db = SessionLocal()
    call = Call(user_id=call_data.user_id, status=call_status)
    db.add(call)
    db.commit()
    db.close()

    # ИСПРАВЛЕНИЕ #6: Отправляем уведомление в Logging Service (Observer pattern)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{LOGGING_SERVICE_URL}/notification",
                json={"event": "call", "status": call_status, "user_id": call_data.user_id})
            await client.post(f"{LOGGING_SERVICE_URL}/log",
                json={"event": "call", "status": call_status, "user_id": call_data.user_id})
    except Exception:
        pass

    # ИСПРАВЛЕНИЕ #4: Инвалидируем кэш при новом звонке
    try:
        redis_client.delete(f"history:{call_data.user_id}")
    except Exception:
        pass

    return {"status": call_status, "user_id": call_data.user_id}


#Получить историю звонков пользователя
# ПРОБЛЕМА №4: Ключи Redis формируются неправильно
@app.get("/history/{user_id}")
async def get_history(user_id: int):
  
    cache_key = f"history:{user_id}"  # ИСПРАВЛЕНИЕ #4: правильный ключ с user_id
    
    # Пытаемся получить из кэша
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    
    # Получаем из БД
    db = SessionLocal()
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()
    
    result = [{"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()} for c in calls]
    
    # Сохраняем в кэш
    import json
    redis_client.setex(cache_key, 60, json.dumps(result))
    
    return result


@app.post("/call/callback")
async def call_callback(callback_data: CallCallback):
    """Callback endpoint для получения статуса звонка от провайдера"""
    db = SessionLocal()
    call = Call(user_id=callback_data.user_id, status=callback_data.status)
    db.add(call)
    db.commit()
    db.close()
    try:
        redis_client.delete(f"history:{callback_data.user_id}")
    except Exception:
        pass
    return {"status": "received"}