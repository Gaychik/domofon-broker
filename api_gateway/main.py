from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv
from jwt_auth import create_token, verify_token, extract_token_from_header
from rate_limiter import rate_limiter

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

# FIX #5: Проверка авторизации через JWT
# FIX #10: Полноценная JWT авторизация вместо X-User-Token
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Пропускаем логин и health без авторизации
    if request.url.path in ["/api/auth/login", "/health", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    # FIX #5 & #10: Проверяем JWT токен из Authorization: Bearer <token>
    try:
        token = extract_token_from_header(request)
        verify_token(token)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    
    # FIX #9: Проверяем rate limiting
    try:
        await rate_limiter.check_rate_limit(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    
    response = await call_next(request)
    return response


# FIX #10: Эндпоинт логина с JWT
@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    # Простая проверка (в продакшене — проверка по БД)
    if username == "admin" and password == "admin123":
        token = create_token(user_id=1, username=username)
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/users")
async def create_user(request: Request):
    #Создание пользователя
    async with httpx.AsyncClient() as client:
        data = await request.json()
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
