from fastapi import FastAPI, HTTPException
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
# ПРОБЛЕМА: Нет проверки на существующий телефон
# ↓ ↓ ↓
# ФИКС: причина: в дб есть уникальность и выдаёт ошибку Internal Server Error, но в свмом коде проверка отсутствует  
# ФИКС: Добавил проверку номера(строка 47-56), теперь выдаёт понятную ошибку


# ПРОБЛЕМА: Не отправляет событие в Logging Service
# ↓ ↓ ↓
# ФИКС: причина: пользователь сразу создавался и ответ сразу возвращался(т.е. события не фиксировалось)
# ФИКС: После сохранения добавил HTTP-запрос в logging_service (строка 48-57)

@app.post("/users")
async def create_user(phone: str, name: str):

    
    db = SessionLocal()

    existing_user = db.query(User).filter(User.phone == phone).first()

    if existing_user:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Номмер уже занят"
        )

    user = User(phone=phone, name=name)

    db.add(user)
    db.commit()
    db.refresh(user)

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{LOGGING_SERVICE_URL}/log",
            json={
                "event": "user_created",
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name
            }
        )

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