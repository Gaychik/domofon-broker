from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import httpx
from dotenv import load_dotenv
from models import Base, User, UserCreate
from sqlalchemy import select

load_dotenv()

app = FastAPI(title="User Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

#Создание пользователя
# ПРОБЛЕМА: Нет проверки на существующий телефон
# ПРОБЛЕМА: Не отправляет событие в Logging Service


@app.post("/users")
async def create_user(user: UserCreate):
    db = SessionLocal()
    existing = db.execute(select(User).where(User.phone == user.phone)).scalar()
    if existing:
        db.close()
        raise HTTPException(status_code=409, detail="Phone already exists")
    user = User(phone=user.phone, name=user.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{LOGGING_SERVICE_URL}/log", json={
                "event": "user_created",
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name
            })
    except Exception:
        pass

    return {"id": user.id, "phone": user.phone, "name": user.name}


#Получение пользователя
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user.id, "phone": user.phone, "name": user.name}