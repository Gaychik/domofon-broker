from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv
from jwt_auth import create_token, verify_token
from rate_limiter import rate_limiter

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
    public_routes = {
        "/api/auth/login",
        "/docs",
        "/openapi.json"
    }

    if request.url.path in public_routes:
        return await call_next(request)

    # rate limiting
    try:
        await rate_limiter.check_rate_limit(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

    # JWT
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Missing or invalid Authorization header"
            }
        )

    token = auth_header.split(" ")[1]

    try:
        request.state.user = verify_token(token)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"detail": str(e)}
        )

    return await call_next(request)


@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == "admin123":
        token = create_token(username=username, user_id=1)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
@app.post("/users")
async def create_user(request: Request):
    #Создание пользователя
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return JSONResponse(status_code=response.status_code, content=response.json())

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    #Получение пользователя
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return JSONResponse(status_code=response.status_code, content=response.json())

@app.post("/call/initiate")
async def initiate_call(request: Request):
    #Инициировать звонок
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
        return JSONResponse(status_code=response.status_code, content=response.json())

@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    #Получить историю звонков
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
        return JSONResponse(status_code=response.status_code, content=response.json())