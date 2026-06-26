from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    phone: str
    name: str


#Создание пользователя
# ПРОБЛЕМА: Нет проверки на существующий телефон
# ПРОБЛЕМА: Не отправляет событие в Logging Service

@app.post("/users")
async def create_user(user_data: UserCreate):

    db = SessionLocal()

    # ИСПРАВЛЕНИЕ #7: Проверка уникальности телефона
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="Phone number already exists")

    user = User(phone=user_data.phone, name=user_data.name)
    db.add(user)
    db.commit()
    db.refresh(user)

    # ИСПРАВЛЕНИЕ #1: Отправляем событие в Logging Service
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{LOGGING_SERVICE_URL}/log",
                json={"event": "user_created", "user_id": user.id, "phone": user.phone}
            )
    except Exception:
        pass

    db.close()
    
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