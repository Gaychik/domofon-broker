from fastapi import FastAPI, Body
import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

# URL Call Service через Docker имя сервиса
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

@app.post("/call")
async def make_call(user_id: int = Body(..., embed=True)):
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