import jwt
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Простое хранилище пользователей (для демонстрации)
USERS_DB = {
    "admin": {"username": "admin", "password": "admin123", "user_id": 1}
}


def create_token(username: str, user_id: int) -> str:
    """Создаёт JWT токен с указанным payload и истечением через 30 минут."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Проверяет JWT токен и возвращает payload. Выбрасывает HTTPException при ошибке."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def authenticate_user(username: str, password: str) -> dict | None:
    """Проверяет учётные данные и возвращает пользователя или None."""
    user = USERS_DB.get(username)
    if user and user["password"] == password:
        return user
    return None
