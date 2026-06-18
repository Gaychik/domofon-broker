from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

# ИСПРАВЛЕНИЕ #3: Правильный URL для Call Service (Docker service name вместо localhost)
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")


class CallRequest(BaseModel):
    user_id: int


@app.post("/call")
async def make_call(call_data: CallRequest):
    #Симуляция внешнего провайдера звонков
    
    # Симуляция обработки звонка
    import asyncio
    await asyncio.sleep(1)  # Симулируем задержку звонка
    
    # Случайный результат звонка
    status = random.choice(["answered", "busy", "no_answer"])
    
    
    # но использует неправильный URL 
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{CALL_SERVICE_URL}/call/callback", json={
                "user_id": call_data.user_id,
                "status": status
            })
        except:
            # Ошибка соединения с Call Service
            pass
    
    return {"status": status, "user_id": call_data.user_id}