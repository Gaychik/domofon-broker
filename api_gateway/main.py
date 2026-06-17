from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from jwt_auth import verify_token, create_token
from rate_limiter import rate_limiter
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PATHS = ["/", "/docs", "/openapi.json", "/api/auth/login"]

@app.middleware("http")
async def auth_and_rate_limit_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    try:
        await rate_limiter.check_rate_limit(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        request.state.user = payload
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Internal server error: {str(e)}"})

    response = await call_next(request)
    return response


class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    if login_data.username == "admin" and login_data.password == "admin123":
        token = create_token({"user_id": 1, "username": login_data.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/users")
async def create_user(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://user_service:8001/users",
            json=await request.json(),
            headers={"Authorization": request.headers.get("Authorization")}
        )
        return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://user_service:8001/users/{user_id}",
            headers={"Authorization": request.headers.get("Authorization")}
        )
        return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/call/initiate")
async def initiate_call(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"http://call_service:8002/call/initiate?user_id={user_id}",
            headers={"Authorization": request.headers.get("Authorization")}
        )

        return JSONResponse(
            status_code=resp.status_code,
            content=resp.json()
        )

@app.get("/history/{user_id}")
async def get_history(user_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"http://call_service:8002/history/{user_id}",
            headers={"Authorization": request.headers.get("Authorization")}
        )
        return JSONResponse(status_code=resp.status_code, content=resp.json())