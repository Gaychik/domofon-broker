from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
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


@app.on_event("startup")
def startup():
    for i in range(30):
        try:
            engine.connect()
            break
        except Exception:
            time.sleep(1)
    Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    phone: str
    name: str


async def log_event(event_type: str, data: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{LOGGING_SERVICE_URL}/log", json={
                "event_type": event_type,
                "service": "user_service",
                **data
            })
    except Exception:
        pass


@app.post("/users")
async def create_user(user: UserCreate):
    db = SessionLocal()

    existing = db.query(User).filter(User.phone == user.phone).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Phone number already exists")

    new_user = User(phone=user.phone, name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    await log_event("user_created", {"user_id": new_user.id, "phone": new_user.phone})

    return {"id": new_user.id, "phone": new_user.phone, "name": new_user.name}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await log_event("user_retrieved", {"user_id": user_id})

    return {"id": user.id, "phone": user.phone, "name": user.name}