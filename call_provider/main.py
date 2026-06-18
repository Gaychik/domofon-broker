from fastapi import FastAPI, Request
import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")


@app.post("/call")
async def make_call(request: Request):
    """Симуляция внешнего провайдера звонков."""
    data = await request.json()
    user_id = data.get("user_id")

    # Симуляция обработки звонка
    import asyncio
    await asyncio.sleep(0.1)  # Уменьшена задержка для тестов

    # Случайный результат звонка
    status = random.choice(["answered", "busy", "no_answer"])

    # Отправляем callback в Call Service
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{CALL_SERVICE_URL}/call/callback",
                json={"user_id": user_id, "status": status},
                timeout=5.0,
            )
        except Exception:
            pass

    return {"status": status, "user_id": user_id}
