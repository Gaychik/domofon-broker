import asyncio
import os
import random

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="Call Provider")

CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")


@app.post("/call")
async def make_call(data: dict):
    user_id = data.get("user_id")
    # Симуляция внешнего провайдера звонков

    await asyncio.sleep(1)  # Симулируем задержку звонка

    # Случайный результат звонка
    status = random.choice(["answered", "busy", "no_answer"])

    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{CALL_SERVICE_URL}/call/callback",
                json={"user_id": user_id, "status": status},
            )
        except:  # noqa: E722
            # Ошибка соединения с Call Service
            pass

    return {"status": status, "user_id": user_id}
