import jwt
from datetime import datetime, timedelta
import os

# JWT авторизация: create_token, verify_token, authenticate_user
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = 30

# Простая база пользователей 
USERS_DB = {
    "admin": "admin123",
    "user": "user123"
}


def create_token(username: str) -> str:
    payload = {
        "user_id": username,
        "username": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def authenticate_user(username: str, password: str) -> str | None:
    if username in USERS_DB and USERS_DB[username] == password:
        return create_token(username)
    return None
