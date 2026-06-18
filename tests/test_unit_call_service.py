import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestCallService:
    """Тесты для Call Service"""

    def test_save_call_to_database(self, call_client):
        """Проблема #2: Call Service должен сохранять звонок в PostgreSQL"""
        client, mock_redis = call_client

        with patch('call_service.main.httpx.AsyncClient') as mock_http:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "answered"}
            mock_client_instance = AsyncMock()
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            response = client.post("/call/initiate", json={"user_id": 1})

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == 1
            assert data["status"] == "answered"

    def test_redis_cache_key_includes_user_id(self, call_client):
        """Проблема #4: Ключ Redis должен содержать user_id"""
        client, mock_redis = call_client

        mock_redis.get.return_value = None

        response = client.get("/history/1")

        mock_redis.get.assert_called_with("history:1")

    def test_redis_cache_hit_returns_cached_data(self, call_client):
        """Проблема #4: При попадании в кэш данные должны возвращаться из Redis"""
        client, mock_redis = call_client

        cached_data = [{"id": 1, "status": "answered", "created_at": "2024-01-01T00:00:00"}]
        mock_redis.get.return_value = json.dumps(cached_data)

        response = client.get("/history/1")

        assert response.status_code == 200
        assert response.json() == cached_data

    def test_redis_cache_set_with_correct_key(self, call_client):
        """Проблема #4: Данные должны сохраняться в кэш с правильным ключом"""
        client, mock_redis = call_client

        mock_redis.get.return_value = None

        response = client.get("/history/5")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "history:5"

    def test_call_sends_notification_to_logging(self, call_client):
        """Проблема #6: При звонке должно отправляться уведомление в Logging Service"""
        client, mock_redis = call_client

        with patch('call_service.main.httpx.AsyncClient') as mock_http:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "answered"}
            mock_client_instance = AsyncMock()
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            response = client.post("/call/initiate", json={"user_id": 1})

            notification_calls = [
                call for call in mock_client_instance.post.call_args_list
                if "/notification" in str(call)
            ]
            assert len(notification_calls) >= 1, "Должен быть вызов /notification в logging_service"

    def test_call_invalidates_cache(self, call_client):
        """Проблема #4: При новом звонке кэш должен инвалидироваться"""
        client, mock_redis = call_client

        with patch('call_service.main.httpx.AsyncClient') as mock_http:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "answered"}
            mock_client_instance = AsyncMock()
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            response = client.post("/call/initiate", json={"user_id": 1})

            mock_redis.delete.assert_called_with("history:1")
