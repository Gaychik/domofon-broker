import pytest
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
import sys
import os

# Добавляем путь к api_gateway, чтобы pytest мог импортировать jwt_auth
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api_gateway')))

from jwt_auth import create_token, verify_token, SECRET_KEY, ALGORITHM

def test_create_and_verify_token():
    """Тест успешного создания и проверки валидного токена"""
    token = create_token(user_id=42, username="test_user")
    assert isinstance(token, str)
    
    # Проверяем, что verify_token возвращает правильный payload
    payload = verify_token(token)
    assert payload["user_id"] == 42
    assert payload["username"] == "test_user"
    assert "exp" in payload
    assert "iat" in payload

def test_verify_expired_token():
    """Тест проверки просроченного токена (должен вернуть 401)"""
    past = datetime.utcnow() - timedelta(hours=1)
    payload = {
        "user_id": 1,
        "username": "admin",
        "iat": past,
        "exp": past + timedelta(minutes=30) # Истек 30 минут назад
    }
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()

def test_verify_invalid_token():
    """Тест проверки поддельного/невалидного токена (должен вернуть 401)"""
    with pytest.raises(HTTPException) as exc_info:
        verify_token("this.is.invalid.token")
    assert exc_info.value.status_code == 401
    assert "invalid" in exc_info.value.detail.lower()