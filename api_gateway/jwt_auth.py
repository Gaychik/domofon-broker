import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status

# Секретный ключ для подписи токенов. 
# В реальном проекте его нужно брать из переменных окружения (.env)!
SECRET_KEY = "super-secret-key-for-domofon-broker-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_token(user_id: int, username: str) -> str:
    """
    Создает JWT токен с заданным payload и временем жизни 30 минут.
    """
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": now,  # Время создания токена (issued at)
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Время истечения
    }
    # Кодируем payload в строку токена
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """
    Проверяет валидность подписи и срок действия JWT токена.
    Возвращает payload, если токен валиден, иначе выбрасывает HTTPException 401.
    """
    try:
        # Декодируем токен и проверяем подпись и exp
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )