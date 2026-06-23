from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging_service:8004")


class CallRequest(BaseModel):
    user_id: int


async def log_event(event_type: str, data: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{LOGGING_SERVICE_URL}/log", json={
                "event_type": event_type,
                "service": "call_provider",
                **data
            })
    except Exception:
        pass  


@app.post("/call")
async def make_call(call: CallRequest):

    import asyncio
    await asyncio.sleep(1)  

 
    status = random.choice(["answered", "busy", "no_answer"])


    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{CALL_SERVICE_URL}/call/callback", json={
                "user_id": call.user_id,
                "status": status
            })
        except Exception:
            pass  

    
    await log_event("call_completed", {"user_id": call.user_id, "status": status})

    return {"status": status, "user_id": call.user_id}