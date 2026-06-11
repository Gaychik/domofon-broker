from fastapi import FastAPI, Request, HTTPException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

# ПРОБЛЕМА: Нет проверки авторизации
# ПРОБЛЕМА: Нет rate limiting

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # TODO: Должна быть проверка JWT токена
    # Сейчас пропускает все запросы без проверки
    response = await call_next(request)
    return response

@app.post("/users")
async def create_user(request: Request):
    #Создание пользователя
    async with httpx.AsyncClient() as client:
        data = await request.json()
        # Проблема: нет проверки rate limiting
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return response.json()

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    #Получение пользователя
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return response.json()

@app.post("/call/initiate")
async def initiate_call(request: Request):
    #Инициировать звонок
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
        return response.json()

@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    #Получить историю звонков
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
        return response.json()