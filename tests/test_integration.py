import pytest
import httpx
import jwt as pyjwt
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


@pytest.mark.skip(reason="Requires running Docker services (docker-compose up)")
class TestIntegration:
    
    @pytest.mark.asyncio
    async def test_full_call_flow(self):
        #Сквозной тест: создание пользователя -> звонок -> история
        
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                "http://localhost:8000/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                user_response = await client.post(
                    "http://localhost:8000/users",
                    json={"phone": "+79991112233", "name": "Integration Test"},
                    headers=headers
                )
                
                if user_response.status_code == 200:
                    user_id = user_response.json().get("id")
                    
                    call_response = await client.post(
                        "http://localhost:8000/call/initiate",
                        json={"user_id": user_id},
                        headers=headers
                    )
                    
                    history_response = await client.get(
                        f"http://localhost:8000/history/{user_id}",
                        headers=headers
                    )
                    
                    assert len(history_response.json()) > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        #FIX #9: Тест rate limiting (требует запущенный сервер)
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                "http://localhost:8000/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                responses = []
                for i in range(20):
                    response = await client.get("http://localhost:8000/users/1", headers=headers)
                    responses.append(response)
                
                status_codes = [r.status_code for r in responses]
                assert 429 in status_codes


class TestJWTAuthIntegration:
    #FIX #10: Тесты JWT авторизации (через TestClient, без реального сервера)
    
    def test_login_returns_token(self, gateway_client):
        response = gateway_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, gateway_client):
        response = gateway_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401
    
    def test_request_without_token_rejected(self, gateway_client):
        response = gateway_client.get("/users/1")
        assert response.status_code == 401
    
    def test_request_with_valid_token_accepted(self, gateway_client, auth_headers):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 1, "phone": "+79991234567", "name": "Test"}
        mock_http_instance = MagicMock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
        mock_http_instance.__aexit__ = AsyncMock(return_value=False)

        with patch('main.httpx.AsyncClient', return_value=mock_http_instance):
            response = gateway_client.get("/users/1", headers=auth_headers)
            assert response.status_code == 200
    
    def test_request_with_expired_token_rejected(self, gateway_client):
        expired_payload = {
            "user_id": 1,
            "username": "admin",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = pyjwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = gateway_client.get(
            "/users/1",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
    
    def test_token_contains_required_fields(self, gateway_client):
        response = gateway_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        data = response.json()
        token = data["access_token"]
        
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "user_id" in payload
        assert "username" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["exp"] - payload["iat"] == 1800

    def test_rate_limiter_returns_429(self, gateway_client, auth_headers):
        """FIX #9: Rate limiter должен возвращать 429 при превышении лимита"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 1}
        mock_http_instance = MagicMock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
        mock_http_instance.__aexit__ = AsyncMock(return_value=False)

        with patch('main.httpx.AsyncClient', return_value=mock_http_instance):
            responses = [gateway_client.get("/users/1", headers=auth_headers) for _ in range(15)]
        
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Rate limiter should return 429 after 10 requests/sec"
