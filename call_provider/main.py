from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

# Исправленный URL для Call Service
CALL_SERVICE_URL = os.getenv(
    "CALL_SERVICE_URL",
    "http://call_service:8002"
)


class CallRequest(BaseModel):
    user_id: int


@app.post("/call")
async def make_call(request: CallRequest):
    """
    Симуляция внешнего провайдера звонков
    """

    user_id = request.user_id

    # Симуляция обработки звонка
    import asyncio
    await asyncio.sleep(1)

    # Случайный результат звонка
    status = random.choice(
        [
            "answered",
            "busy",
            "no_answer"
        ]
    )

    return {
        "status": status,
        "user_id": user_id
    }