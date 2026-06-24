from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
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

# 1. Создаем Pydantic-модель для корректного парсинга JSON из тела запроса
class UserCreate(BaseModel):
    phone: str
    name: str

# Создание пользователя
@app.post("/users")
async def create_user(user_data: UserCreate):
    db = SessionLocal()
    try:
        # 2. Проверяем, нет ли пользователя с таким телефоном
        existing_user = db.query(User).filter(User.phone == user_data.phone).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Phone number already exists")
            
        user = User(phone=user_data.phone, name=user_data.name)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 3. Отправка события в Logging Service
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{LOGGING_SERVICE_URL}/log", 
                    json={
                        "event": "user_created",
                        "user_id": user.id,
                        "phone": user.phone,
                        "name": user.name
                    },
                    timeout=5.0
                )
        except Exception as e:
            # Если лог-сервис недоступен, мы не должны падать с ошибкой 500 для клиента.
            # Просто выводим предупреждение в консоль.
            print(f"Failed to send log event to Logging Service: {e}")
            
        return {"id": user.id, "phone": user.phone, "name": user.name}
        
    finally:
        # 4. Гарантированно закрываем сессию БД даже в случае ошибки
        db.close()

# Получение пользователя
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "phone": user.phone, "name": user.name}
    finally:
        db.close()