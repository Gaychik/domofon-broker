import pytest
import jwt
from datetime import datetime, timedelta, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api_gateway'))

from api_gateway.jwt_auth import create_token, verify_token, authenticate_user, SECRET_KEY, ALGORITHM


class TestJWTAuth:
    #Тесты для JWT авторизации

    def test_jwt_token_creation(self):
        token = create_token(username="admin", user_id=1)
        assert token is not None
        assert isinstance(token, str)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["username"] == "admin"
        assert payload["user_id"] == 1
        assert "exp" in payload
        assert "iat" in payload

    def test_jwt_token_validation(self):
        token = create_token(username="admin", user_id=1)
        payload = verify_token(token)
        assert payload["username"] == "admin"
        assert payload["user_id"] == 1

    def test_token_expiration(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_payload = {
            "user_id": 1, "username": "admin",
            "exp": past, "iat": past - timedelta(minutes=30),
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_rejected(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_token_contains_required_fields(self):
        token = create_token(username="testuser", user_id=42)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "user_id" in payload
        assert "username" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["user_id"] == 42
        assert payload["username"] == "testuser"

    def test_token_expires_in_30_minutes(self):
        token = create_token(username="admin", user_id=1)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        assert exp - iat == timedelta(minutes=30)

    def test_authenticate_user_valid(self):
        user = authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"

    def test_authenticate_user_invalid_password(self):
        user = authenticate_user("admin", "wrongpassword")
        assert user is None

    def test_authenticate_user_not_found(self):
        user = authenticate_user("nonexistent", "password")
        assert user is None


class TestGatewayAuth:
    """Тесты авторизации API Gateway (Проблемы #5, #9, #10)"""

    def test_request_without_token_returns_401(self, gateway_client):
        response = gateway_client.get("/users/1")
        assert response.status_code == 401

    def test_request_with_invalid_token_returns_401(self, gateway_client):
        response = gateway_client.get(
            "/users/1", headers={"Authorization": "Bearer invalid.token"}
        )
        assert response.status_code == 401

    def test_login_endpoint_returns_token(self, gateway_client):
        response = gateway_client.post(
            "/api/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials_returns_401(self, gateway_client):
        response = gateway_client.post(
            "/api/auth/login", json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_request_with_valid_token_passes(self, gateway_client, auth_headers):
        response = gateway_client.get("/users/1", headers=auth_headers)
        assert response.status_code != 401

    def test_login_without_credentials_returns_400(self, gateway_client):
        response = gateway_client.post("/api/auth/login", json={})
        assert response.status_code == 400
