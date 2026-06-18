from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import time
from collections import defaultdict
from dotenv import load_dotenv
from jwt_auth import create_token, verify_token
import jwt as pyjwt

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

# ── Rate limiting: 10 запросов в секунду на IP ──
RATE_LIMIT = 10  # макс. запросов
RATE_WINDOW = 1  # в секунду
_request_log: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    now = time.time()
    # Оставляем только запросы за последнюю секунду
    _request_log[client_ip] = [
        t for t in _request_log[client_ip] if now - t < RATE_WINDOW
    ]
    if len(_request_log[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    _request_log[client_ip].append(now)


# ── JWT Middleware (Problem 5 + Problem 10) ──
PUBLIC_PATHS = {"/api/auth/login", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Rate limiting (Problem 9)
    client_ip = request.client.host if request.client else "unknown"
    try:
        _check_rate_limit(client_ip)
    except HTTPException:
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

    # Пропускаем публичные эндпоинты
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # Проверка JWT токена (Problem 5 + 10)
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid Authorization header. Expected: Bearer <token>"},
        )

    token = auth_header[len("Bearer "):]
    try:
        payload = verify_token(token)
        # Сохраняем payload в state для downstream
        request.state.user = payload
    except pyjwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Token expired"})
    except pyjwt.InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": f"Invalid token: {e}"})

    response = await call_next(request)
    return response


# ── Auth endpoint (Problem 10) ──
@app.post("/api/auth/login")
async def login(request: Request):
    """Простой логин: admin/admin123. Возвращает JWT токен."""
    data = await request.json()
    username = data.get("username", "")
    password = data.get("password", "")

    # Простая проверка учётных данных
    if username == "admin" and password == "admin123":
        token = create_token(user_id=1, username=username)
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")


# ── Users ──
@app.post("/users")
async def create_user(request: Request):
    """Создание пользователя"""
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(
            f"{USER_SERVICE_URL}/users",
            json=data,
            timeout=10.0,
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )


@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    """Получение пользователя"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USER_SERVICE_URL}/users/{user_id}",
            timeout=10.0,
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )


# ── Calls ──
@app.post("/call/initiate")
async def initiate_call(request: Request):
    """Инициировать звонок"""
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(
            f"{CALL_SERVICE_URL}/call/initiate",
            json=data,
            timeout=15.0,
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )


@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    """Получить историю звонков"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CALL_SERVICE_URL}/history/{user_id}",
            timeout=10.0,
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )
