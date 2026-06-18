import jwt
import os
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = 30


def create_token(user_id: int, username: str) -> str:
    """Создаёт JWT токен с payload: user_id, username, exp, iat."""
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Проверяет JWT токен и возвращает payload. Выбрасывает исключение при ошибке."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
