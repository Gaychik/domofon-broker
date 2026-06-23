import pytest
from fastapi.testclient import TestClient
import sys
import os
import uuid
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUserService:
    # Тест успешного создания пользователя
    def test_create_user_success(self, user_client):
        phone = f"test_{uuid.uuid4().hex[:8]}"

        with patch("user_service.main.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            response = user_client.post(
                f"/users?phone={phone}&name=TestUser"
            )

        assert response.status_code == 200
        data = response.json()

        assert data["phone"] == phone
        assert data["name"] == "TestUser"
        assert "id" in data

    # Тест получения существующего пользователя
    def test_get_user_success(self, user_client):
        phone = f"test_{uuid.uuid4().hex[:8]}"

        with patch("user_service.main.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            create_response = user_client.post(
                f"/users?phone={phone}&name=TestUser"
            )

        user_id = create_response.json()["id"]

        response = user_client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user_id
        assert data["phone"] == phone

    # Тест возврата ошибки при запросе несуществующего пользователя
    def test_get_user_not_found(self, user_client):
        response = user_client.get("/users/999999")

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    # Тест проверки уникальности номера телефона
    def test_duplicate_phone_returns_400(self, user_client):
        phone = f"test_{uuid.uuid4().hex[:8]}"

        with patch("user_service.main.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            first_response = user_client.post(
                f"/users?phone={phone}&name=User1"
            )

            second_response = user_client.post(
                f"/users?phone={phone}&name=User2"
            )

        assert first_response.status_code == 200
        assert second_response.status_code == 400

    # Тест отправки события в Logging Service при создании пользователя
    def test_create_user_sends_log_event(self, user_client):
        phone = f"test_{uuid.uuid4().hex[:8]}"

        with patch("user_service.main.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            response = user_client.post(
                f"/users?phone={phone}&name=LogUser"
            )

            assert response.status_code == 200
            assert mock_instance.post.called