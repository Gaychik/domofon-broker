import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from rate_limiter import rate_limiter

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    try:
        await rate_limiter.check_rate_limit(request=request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    if not (request.url.path == "/users" and request.method == "POST"):
        token = request.headers.get("X-User-Token")
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Вы не авторизованы!"},
            )

    response = await call_next(request)
    return response


@app.post("/users")
async def create_user(request: Request):
    # Создание пользователя
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return response.json()


@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    # Получение пользователя
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return response.json()


@app.post("/call/initiate")
async def initiate_call(request: Request):
    # Инициировать звонок
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
        return response.json()


@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    # Получить историю звонков
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
        return response.json()
