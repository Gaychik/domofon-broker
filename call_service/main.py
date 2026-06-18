from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://call_provider:8003") 

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

# Проблема: Redis подключен, но не используется правильно
redis_client = redis.from_url(REDIS_URL)


#Инициировать звонок
# FIX #2: Сохраняет звонок в PostgreSQL
# FIX #6: Отправляет уведомление о звонке (Observer pattern)
@app.post("/call/initiate")
async def initiate_call(user_id: int):
   
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{PROVIDER_URL}/call", json={"user_id": user_id})
            call_status = response.json().get("status", "unknown")
        except:
            call_status = "failed"
    
    # FIX #2: Сохраняем звонок в БД
    db = SessionLocal()
    call = Call(user_id=user_id, status=call_status)
    db.add(call)
    db.commit()
    db.refresh(call)
    db.close()
    
    # FIX #6: Observer pattern — уведомляем logging_service
    try:
        import json as _json
        async with httpx.AsyncClient() as client:
            await client.post("http://logging_service:8004/notification", json={"event": "call", "status": call_status, "user_id": user_id})
    except Exception:
        pass  # Не ломаем звонок, если логгинг недоступен
    
    return {"status": call_status, "user_id": user_id}


#Получить историю звонков пользователя
# FIX #4: Ключи Redis формируются правильно (включают user_id)
@app.get("/history/{user_id}")
async def get_history(user_id: int):
  
    import json
    cache_key = f"history:{user_id}"  # FIX #4: Добавлен user_id в ключ кэша
    
    # Пытаемся получить из кэша
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Получаем из БД
    db = SessionLocal()
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()
    
    result = [{"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()} for c in calls]
    
    # Сохраняем в кэш
    redis_client.setex(cache_key, 60, json.dumps(result))
    
    return result