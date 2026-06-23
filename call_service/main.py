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

# Проблема: Redis подключен, но не используется правильно
redis_client = redis.from_url(REDIS_URL)


#Инициировать звонок
# ПРОБЛЕМА №2: Не сохраняет звонок в PostgreSQL
# ПРОБЛЕМА: Не отправляет событие в Logging Service
# ↓ ↓ ↓
# ФИКС: причина: отсутствует код, который сохраняет историю звонков в бд
# ФИКС: добавил код который сохраняет историю звонков в бд (изменения строка 58-66)

# ПРОБЛЕМА №6: Не отправляет уведомление о звонке
# ↓ ↓ ↓
# ФИКС: причина: отсутствие url: LOGGING_SERVICE и его вызова
# ФИКС: добавил url(строка 18) и вызов(строка 73-81), так же заменил json={"user_id": user_id}) на params={"user_id": user_id})

@app.post("/call/initiate")
async def initiate_call(user_id: int):
   
    async with httpx.AsyncClient() as client:
        try:
            # Проблема: PROVIDER_URL может быть недоступен из-за неправильного имени сервиса
            response = await client.post(f"{PROVIDER_URL}/call", params={"user_id": user_id})
            call_status = response.json().get("status", "unknown")
        except:
            call_status = "failed"
    
    db = SessionLocal()

    call = Call(
        user_id=user_id,
        status=call_status
    )

    db.add(call)
    db.commit()
    db.refresh(call)
    db.close()
  
    if call_status == "answered":
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{LOGGING_SERVICE_URL}/notification",
                json={
                    "event": "call",
                    "status": "answered"
                }
            )
    
    return {"status": call_status, "user_id": user_id}


#Получить историю звонков пользователя
# ПРОБЛЕМА №4: Ключи Redis формируются неправильно
# ↓ ↓ ↓
# ФИКС: Причинна: для всех пользователей использовался 1 и тот же ключ
# ФМКС: добавлен индетификатор {user_id} благодаря чему для каждого пользователя есть свой ключ(польз.1 - history1 и т.п.)
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
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()
    
    result = [{"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()} for c in calls]
    
    # Сохраняем в кэш
    import json
    redis_client.setex(cache_key, 60, json.dumps(result))
    
    return result