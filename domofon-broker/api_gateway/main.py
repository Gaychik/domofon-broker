from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import jwt
import os
from dotenv import load_dotenv
from rate_limiter import rate_limiter

load_dotenv()

app = FastAPI(title="API Gateway")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "http://call_service:8002")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

PUBLIC_PATHS = ["/docs", "/openapi.json", "/redoc"]


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    rate_limited = await rate_limiter.check_rate_limit(request)
    if rate_limited:
        return rate_limited

    if request.url.path in PUBLIC_PATHS:
        response = await call_next(request)
        return response

    token = request.headers.get("X-User-Token")
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Missing X-User-Token header"})

    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Token has expired"})
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    response = await call_next(request)
    return response


@app.post("/users")
async def create_user(request: Request):
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/call/initiate")
async def initiate_call(request: Request):
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/initiate", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/call/callback")
async def call_callback(request: Request):
    async with httpx.AsyncClient() as client:
        data = await request.json()
        response = await client.post(f"{CALL_SERVICE_URL}/call/callback", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CALL_SERVICE_URL}/history/{user_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)