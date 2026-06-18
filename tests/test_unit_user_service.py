import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUserService:
    """Тесты для User Service"""

    def test_create_user_success(self, user_client):
        """Тест успешного создания пользователя"""
        client = user_client

        with patch('user_service.main.httpx.AsyncClient') as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_http_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.post = AsyncMock(return_value=MagicMock(status_code=200))

            response = client.post("/users", json={"phone": "+79991111111", "name": "Test"})

            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == "+79991111111"
            assert data["name"] == "Test"
            assert "id" in data

    def test_create_user_sends_log_event(self, user_client):
        """Проблема #1: User Service должен отправлять событие в Logging Service"""
        client = user_client

        with patch('user_service.main.httpx.AsyncClient') as mock_http_client:
            mock_client_instance = AsyncMock()
            mock_http_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            response = client.post("/users", json={"phone": "+79992222222", "name": "LogTest"})

            post_calls = [
                call for call in mock_client_instance.post.call_args_list
                if "/log" in str(call)
            ]
            assert len(post_calls) >= 1, "Должен быть вызов /log в logging_service"

    def test_create_user_duplicate_phone_returns_400(self, user_client):
        """Проблема #7: User Service должен отклонять дубликаты телефонов"""
        client = user_client

        with patch('user_service.main.httpx.AsyncClient'):
            client.post("/users", json={"phone": "+79993333333", "name": "User1"})

        response = client.post(
            "/users",
            json={"phone": "+79993333333", "name": "User2"}
        )

        assert response.status_code == 400
        assert "Phone number already exists" in response.json()["detail"]

    def test_get_user_returns_user(self, user_client):
        """Тест получения пользователя"""
        client = user_client

        with patch('user_service.main.httpx.AsyncClient'):
            create_resp = client.post("/users", json={"phone": "+79994444444", "name": "GetTest"})

        user_id = create_resp.json()["id"]

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["phone"] == "+79994444444"

    def test_get_user_not_found_returns_404(self, user_client):
        """Тест: пользователь не найден"""
        client = user_client
        response = client.get("/users/99999")
        assert response.status_code == 404
