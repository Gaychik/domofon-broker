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

# --- ЭТО ГЛАВНОЕ: модель для JSON-тела ---
class UserCreate(BaseModel):
    phone: str
    name: str

@app.post("/users")
def create_user(user: UserCreate):   # ← принимаем JSON
    db = SessionLocal()
    existing = db.query(User).filter(User.phone == user.phone).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Phone already exists")

    new_user = User(phone=user.phone, name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        with httpx.Client() as client:
            client.post(
                f"{LOGGING_SERVICE_URL}/log",
                json={
                    "event": "user_created",
                    "user_id": new_user.id,
                    "phone": new_user.phone,
                    "name": new_user.name
                }
            )
    except Exception:
        pass

    db.close()
    return {"id": new_user.id, "phone": new_user.phone, "name": new_user.name}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "phone": user.phone, "name": user.name}