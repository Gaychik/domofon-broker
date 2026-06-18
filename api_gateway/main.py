from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import sys
from dotenv import load_dotenv

# Подключаем rate_limiter и jwt_auth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rate_limiter import rate_limiter
from jwt_auth import verify_token, authenticate_user

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

# Middleware: rate limiter (10 req/sec) + JWT Bearer авторизация

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Пропускаем служебные пути и логин
    if request.url.path in ("/docs", "/openapi.json", "/api/auth/login"):
        return await call_next(request)

    # Rate limiting
    try:
        await rate_limiter.check_rate_limit(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    # Проверка JWT Bearer токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: missing or invalid token"})

    token = auth_header.split("Bearer ")[1]
    payload = verify_token(token)
    if payload is None:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: invalid or expired token"})

    response = await call_next(request)
    return response


@app.post("/api/auth/login")
async def login(request: Request):
    """Эндпоинт для получения JWT токена"""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    token = authenticate_user(username, password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/users")
async def create_user(request: Request):
    #Создание пользователя
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    #Получение пользователя
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/call/initiate")
async def initiate_call(request: Request):
    #Инициировать звонок
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    #Получить историю звонков
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)