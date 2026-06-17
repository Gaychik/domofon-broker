from fastapi import FastAPI, Request
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import redis
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Service")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://domofon:domofon123@postgres:5432/domofon"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

PROVIDER_URL = os.getenv(
    "PROVIDER_URL",
    "http://call_provider:8003"
)

LOGGING_SERVICE_URL = os.getenv(
    "LOGGING_SERVICE_URL",
    "http://logging_service:8004"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

redis_client = redis.from_url(REDIS_URL)


# =========================
# CALL INITIATE
# =========================
@app.post("/call/initiate")
async def initiate_call(request: Request):

    user_id = None

    # 1. пробуем JSON
    try:
        body = await request.json()
        user_id = body.get("user_id")
    except Exception:
        pass

    # 2. если JSON нет — берём query params
    if user_id is None:
        user_id = request.query_params.get("user_id")

    user_id = int(user_id)

    call_status = "unknown"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PROVIDER_URL}/call",
                json={"user_id": user_id}
            )

            try:
                data = response.json()
            except Exception:
                data = {}

            raw_status = data.get("status", "unknown")

            if raw_status in ["no_answer", "missed", "timeout"]:
                call_status = "answered"
            else:
                call_status = raw_status

        except Exception:
            call_status = "failed"

    db = SessionLocal()

    call = Call(user_id=user_id, status=call_status)

    db.add(call)
    db.commit()

    db.close()

    return {
        "status": call_status,
        "user_id": user_id
    }
# =========================
# HISTORY
# =========================
@app.get("/history/{user_id}")
async def get_history(user_id: int):

    cache_key = f"history:{user_id}"

    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    db = SessionLocal()
    calls = db.query(Call).filter(Call.user_id == user_id).all()
    db.close()

    result = [
        {
            "id": c.id,
            "status": c.status,
            "created_at": c.created_at.isoformat()
        }
        for c in calls
    ]

    import json
    redis_client.setex(cache_key, 60, json.dumps(result))

    return result