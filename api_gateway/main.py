from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel  # ✅ Убедитесь, что эта строка есть!
import httpx
import os
from dotenv import load_dotenv
from rate_limiter import rate_limiter
from jwt_auth import create_token, verify_token

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")

# Пути, которые не требуют авторизации
PUBLIC_PATHS = ["/docs", "/openapi.json", "/redoc", "/health", "/api/auth/login"]

class LoginRequest(BaseModel):
    username: str
    password: str

# ✅ 1. Эндпоинт для получения JWT токена
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # В реальном проекте здесь был бы запрос в User Service для проверки пароля.
    # Для учебного проекта используем хардкод, как указано в ТЗ.
    if request.username == "admin" and request.password == "admin123":
        # Генерируем токен (user_id=1 для админа)
        token = create_token(user_id=1, username=request.username)
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.middleware("http")
async def auth_and_rate_limit_middleware(request: Request, call_next):
    # 1. Пропускаем публичные пути (Swagger, health check)
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    
    # # 2. Проверка авторизации (X-User-Token) # ////////////// вернись похорошему удалить мб забыл
    # token = request.headers.get("X-User-Token")
    # if not token or token.strip() == "":
    #     raise HTTPException(
    #         status_code=401,
    #         detail="Unauthorized: Missing or empty X-User-Token header"
    #     )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Извлекаем сам токен (убираем "Bearer ")
    token = auth_header.split(" ")[1]
    
    # Проверяем токен (если невалиден или истек - verify_token сам вернет 401)
    verify_token(token)

    # 3. ✅ Проверка Rate Limiting (10 запросов в секунду)
    await rate_limiter.check_rate_limit(request)
    
    # 4. Если всё ок — пропускаем запрос дальше
    response = await call_next(request)
    return response


@app.post("/users")
async def create_user(request: Request):
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return response.json()


@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return response.json()


@app.post("/call/initiate")
async def initiate_call(request: Request):
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
        return response.json()


@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
        return response.json()
    
