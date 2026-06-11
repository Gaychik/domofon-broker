from fastapi import FastAPI
import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

# ПРОБЛЕМА: Неправильный URL для Call Service
# ПРОБЛЕМА: Пытается отправить результат обратно в Call Service,
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://localhost:8002")

@app.post("/call")
async def make_call(user_id: int):
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
                "user_id": user_id,
                "status": status
            })
        except:
            # Ошибка соединения с Call Service
            pass
    
    return {"status": status, "user_id": user_id}