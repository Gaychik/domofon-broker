import pytest
import jwt
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api_gateway'))
from jwt_auth import create_token, verify_token, authenticate_user, JWT_SECRET_KEY, JWT_ALGORITHM


class TestJWTAuth:

    def test_jwt_token_creation(self):
        """Создание JWT токена"""
        token = create_token("admin")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_token_validation(self):
        """Валидация JWT токена"""
        token = create_token("admin")
        payload = verify_token(token)
        assert payload is not None
        assert payload["username"] == "admin"

    def test_token_expiration(self):
        """Токен истёк — verify возвращает None"""
        expired_payload = {
            "user_id": "admin",
            "username": "admin",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        assert verify_token(expired_token) is None

    def test_invalid_token(self):
        """Невалидный токен — None"""
        assert verify_token("not.a.valid.token") is None

    def test_authenticate_success(self):
        """Успешная аутентификация"""
        token = authenticate_user("admin", "admin123")
        assert token is not None
        assert verify_token(token)["username"] == "admin"

    def test_authenticate_wrong_password(self):
        """Неверный пароль — None"""
        assert authenticate_user("admin", "wrongpass") is None

    def test_authenticate_unknown_user(self):
        """Неизвестный пользователь — None"""
        assert authenticate_user("hacker", "any") is None

    def test_token_payload_fields(self):
        """Payload содержит нужные поля"""
        token = create_token("user")
        payload = verify_token(token)
        assert "user_id" in payload
        assert "username" in payload
        assert "exp" in payload
        assert "iat" in payload
