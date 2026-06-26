from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv

from jwt_auth import create_token, verify_token, authenticate_user
from rate_limiter import rate_limiter

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

# ИСПРАВЛЕНИЕ #5 + #9 + #10: Авторизация + rate limiting
PUBLIC_PATHS = ["/api/auth/login", "/docs", "/openapi.json", "/redoc"]

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # ИСПРАВЛЕНИЕ #9: Rate limiting
    try:
        await rate_limiter.check_rate_limit(request)
    except HTTPException:
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

    # ИСПРАВЛЕНИЕ #5: Пропускаем публичные пути
    if request.url.path in PUBLIC_PATHS:
        response = await call_next(request)
        return response

    # ИСПРАВЛЕНИЕ #10: Проверяем JWT токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid Authorization header. Use 'Bearer <token>'"}
        )

    token = auth_header.split(" ", 1)[1]
    try:
        payload = verify_token(token)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    request.state.user = payload
    response = await call_next(request)
    return response


# ИСПРАВЛЕНИЕ #10: Эндпоинт для получения JWT токена
@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(username=user["username"], user_id=user["user_id"])
    return {"access_token": token, "token_type": "bearer"}

@app.post("/users")
async def create_user(request: Request):
    #Создание пользователя
    async with httpx.AsyncClient() as client:
        data = await request.json()
        try:
            response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
            try:
                resp_data = response.json()
            except Exception:
                resp_data = {"detail": response.text or "Service error"}
            if response.status_code >= 400:
                return JSONResponse(status_code=response.status_code, content=resp_data)
            return resp_data
        except Exception:
            return JSONResponse(status_code=503, content={"detail": "User service unavailable"})

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    #Получение пользователя
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text or "Service error"}
            if response.status_code >= 400:
                return JSONResponse(status_code=response.status_code, content=data)
            return data
        except Exception:
            return JSONResponse(status_code=503, content={"detail": "User service unavailable"})

@app.post("/call/initiate")
async def initiate_call(request: Request):
    #Инициировать звонок
    async with httpx.AsyncClient() as client:
        data = await request.json()
        try:
            response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
            try:
                resp_data = response.json()
            except Exception:
                resp_data = {"detail": response.text or "Service error"}
            if response.status_code >= 400:
                return JSONResponse(status_code=response.status_code, content=resp_data)
            return resp_data
        except Exception:
            return JSONResponse(status_code=503, content={"detail": "Call service unavailable"})

@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    #Получить историю звонков
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
            try:
                resp_data = response.json()
            except Exception:
                resp_data = {"detail": response.text or "Service error"}
            if response.status_code >= 400:
                return JSONResponse(status_code=response.status_code, content=resp_data)
            return resp_data
        except Exception:
            return JSONResponse(status_code=503, content={"detail": "Call service unavailable"})