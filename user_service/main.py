from fastapi import FastAPI, HTTPException, Body
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="User Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)

#Создание пользователя
# Проверка уникальности телефона + логирование в Logging Service

@app.post("/users")
async def create_user(phone: str = Body(...), name: str = Body(...)):

    # Проверка уникальности телефона
    db = SessionLocal()
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Phone already exists")

    user = User(phone=phone, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    # Отправляем событие в Logging Service
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{LOGGING_SERVICE_URL}/log", json={
                "event": "user_created",
                "user_id": user.id,
                "phone": user.phone
            })
        except:
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