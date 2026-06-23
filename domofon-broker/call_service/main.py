from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import httpx
import os
import json
import time
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


redis_client = None


@app.on_event("startup")
def startup():
    global redis_client
    for i in range(30):
        try:
            engine.connect()
            break
        except Exception:
            time.sleep(1)
    Base.metadata.create_all(bind=engine)
    for i in range(30):
        try:
            redis_client = redis.from_url(REDIS_URL)
            redis_client.ping()
            break
        except Exception:
            time.sleep(1)


class CallInitiate(BaseModel):
    user_id: int


class CallCallback(BaseModel):
    user_id: int
    status: str


async def log_event(event_type: str, data: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{LOGGING_SERVICE_URL}/log", json={
                "event_type": event_type,
                "service": "call_service",
                **data
            })
    except Exception:
        pass


@app.post("/call/initiate")
async def initiate_call(call: CallInitiate):
    db = SessionLocal()
    new_call = Call(user_id=call.user_id, status="initiated")
    db.add(new_call)
    db.commit()
    db.refresh(new_call)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{PROVIDER_URL}/call", json={"user_id": call.user_id})
            call_status = response.json().get("status", "unknown")
        except Exception:
            call_status = "failed"

    # Update call status in DB
    new_call.status = call_status
    db.commit()
    db.refresh(new_call)
    db.close()

    cache_key = f"history:{call.user_id}"
    redis_client.delete(cache_key)

    await log_event("call_initiated", {"call_id": new_call.id, "user_id": call.user_id, "status": call_status})

    return {"id": new_call.id, "status": call_status, "user_id": call.user_id}


@app.post("/call/callback")
async def call_callback(data: CallCallback):
    db = SessionLocal()
    call = db.query(Call).filter(Call.user_id == data.user_id).order_by(Call.id.desc()).first()

    if call:
        call.status = data.status
        db.commit()
        db.refresh(call)

        cache_key = f"history:{data.user_id}"
        redis_client.delete(cache_key)

        await log_event("call_callback", {"call_id": call.id, "user_id": data.user_id, "status": data.status})

    db.close()
    return {"status": "updated"}


@app.get("/history/{user_id}")
async def get_history(user_id: int):
    cache_key = f"history:{user_id}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    db = SessionLocal()
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()

    result = [{"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()} for c in calls]

    redis_client.setex(cache_key, 60, json.dumps(result))

    return result