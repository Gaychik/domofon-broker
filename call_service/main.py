import json
import os

import httpx
import redis
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from models import Base, Call
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

app = FastAPI(title="Call Service")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://domofon:domofon123@postgres:5432/domofon"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://call_provider:8003")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

redis_client = redis.from_url(REDIS_URL)


@app.post("/call/initiate")
async def initiate_call(data: dict):
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Необходим user_id"
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PROVIDER_URL}/call", json={"user_id": user_id}
            )
            call_status = response.json().get("status", "unknown")
        except:  # noqa: E722
            call_status = "failed"

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{LOGGING_SERVICE_URL}/log",
            json={
                "service": "call_service",
                "event": "call_initiated",
                "data": {"user_id": user_id, "status": call_status},
            },
        )

    return {"user_id": user_id, "call_status": call_status}


@app.post("/call/callback")
async def get_response(data: dict):
    user_id = data.get("user_id")
    call_status = data.get("status")

    db = SessionLocal()
    call = Call(user_id=user_id, status=call_status)
    db.add(call)
    db.commit()
    db.refresh(call)
    db.close()

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{LOGGING_SERVICE_URL}/log",
            json={
                "service": "call_service",
                "event": "call_completed",
                "data": {"user_id": user_id, "status": call_status},
            },
        )

    redis_client.delete(f"history:{user_id}")

    return {"status": call_status, "user_id": user_id}


# Получить историю звонков пользователя
@app.get("/history/{user_id}")
async def get_history(user_id: int):

    cache_key = f"history:{user_id}"

    # Пытаемся получить из кэша
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Получаем из БД
    db = SessionLocal()
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()

    result = [
        {"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()}
        for c in calls
    ]

    redis_client.setex(cache_key, 60, json.dumps(result))

    return result
