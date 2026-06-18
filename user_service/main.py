from fastapi import FastAPI, HTTPException, Request
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


@app.post("/users")
async def create_user(request: Request):
    """Создание пользователя с проверкой уникальности телефона и логированием."""
    data = await request.json()
    phone = data.get("phone", "")
    name = data.get("name", "")

    db = SessionLocal()
    try:
        # Problem 7: Проверка уникальности телефона
        existing = db.query(User).filter(User.phone == phone).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Phone number already exists")

        user = User(phone=phone, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

        result = {"id": user.id, "phone": user.phone, "name": user.name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    # Problem 1: Отправляем событие в Logging Service
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{LOGGING_SERVICE_URL}/log",
                json={"event": "user_created", "user_id": result["id"], "phone": result["phone"]},
                timeout=5.0,
            )
    except Exception:
        pass  # Логирование не должно блокировать основной поток

    return result


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Получение пользователя."""
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": user.id, "phone": user.phone, "name": user.name}
