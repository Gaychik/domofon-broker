from fastapi import FastAPI
from pydantic import BaseModel
import os
import random
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Provider")

# ✅ Pydantic-модель для приёма JSON-тела
class CallRequest(BaseModel):
    user_id: int


@app.post("/call")
async def make_call(request: CallRequest):
    user_id = request.user_id
    
    # Симуляция обработки звонка (задержка)
    await asyncio.sleep(1)  
    
    # Случайный результат звонка
    status = random.choice(["answered", "busy", "no_answer"])
    
    # Возвращаем результат синхронно
    return {"status": status, "user_id": user_id}