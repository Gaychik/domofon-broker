from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv
from models import Base, Call, CallbackRequest, CallInitiateRequest
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Call Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://call_provider:8003")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Проблема: Redis подключен, но не используется правильно
redis_client = redis.from_url(REDIS_URL)

@app.post("/call/initiate")
async def initiate_call(request: CallInitiateRequest):
    user_id = request.user_id
    
    async with httpx.AsyncClient() as client:
        try:
            # Проблема: PROVIDER_URL может быть недоступен из-за неправильного имени сервиса
            response = await client.post(f"{PROVIDER_URL}/call", json={"user_id": user_id})
            call_status = response.json().get("status", "unknown")
        except:
            call_status = "failed"
    
    db = SessionLocal()
    try:
        call = Call(user_id=user_id, status=call_status)
        db.add(call)
        db.commit()
    finally:
        db.close()
    
    redis_client.delete(f"history:{user_id}")
    
    if call_status == "answered":
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{LOGGING_SERVICE_URL}/notification",
                    json={"event": "call", "status": "answered"}
                )
        except:
            pass
    
    return {"status": call_status, "user_id": user_id}


#Получить историю звонков пользователя
# ПРОБЛЕМА №4: Ключи Redis формируются неправильно
@app.get("/history/{user_id}")
async def get_history(user_id: int):
    cache_key = f"history:{user_id}"
    
    # Пытаемся получить из кэша
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    
    # Получаем из БД
    db = SessionLocal()
    try:
        calls = db.query(Call).filter(Call.user_id == user_id).all()
    finally:
        db.close()
    
    result = [{"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()} for c in calls]
    
    # Сохраняем в кэш
    import json
    redis_client.setex(cache_key, 60, json.dumps(result))
    
    return result

@app.post("/call/callback")
async def call_callback(request: CallbackRequest):
    db = SessionLocal()
    try:
        call = Call(user_id=request.user_id, status=request.status)
        db.add(call)
        db.commit()
        redis_client.delete(f"history:{request.user_id}")
        return {"status": request.status, "user_id": request.user_id}
    finally:
        db.close()