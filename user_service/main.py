import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from models import Base, User
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

load_dotenv()

app = FastAPI(title="User Service")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon"
)
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass  # БД недоступна — тесты запущены без docker-compose


@app.post("/users")
async def create_user(data: dict):
    phone = data.get("phone")
    name = data.get("name")
    db = SessionLocal()
    existing_user = db.execute(select(User).where(User.phone == phone))
    if existing_user.scalar():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким номером телефона уже существует!",
        )

    user = User(phone=phone, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    async with httpx.AsyncClient() as client:
        await client.post(
            url=f"{LOGGING_SERVICE_URL}/log",
            json={
                "service": "user_service",
                "event": "user_created",
                "data": {"id": user.id, "phone": user.phone, "name": user.name},
            },
        )

    return {"id": user.id, "phone": user.phone, "name": user.name}


# Получение пользователя
@app.get("/users/{user_id}")
async def get_user(user_id: int):

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": user.id, "phone": user.phone, "name": user.name}
