import pytest
from unittest.mock import patch, MagicMock


class TestCallService:

    def test_save_call_to_database(self, call_client):
        """Fix #2: сохранение звонка в БД"""
        with patch('call_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            with patch('httpx.AsyncClient') as mock_http:
                mock_response = MagicMock()
                mock_response.json.return_value = {"status": "answered"}
                mock_http.return_value.__aenter__.return_value.post.return_value = mock_response

                response = call_client.post("/call/initiate", json={"user_id": 1})

                # Проверяем, что был вызов commit (сохранение в БД)
                mock_db.commit.assert_called_once()

    def test_redis_cache_used(self, call_client):
        """Fix #4: Redis использует правильный ключ history:{user_id}"""
        with patch('call_service.main.redis_client') as mock_redis:
            mock_redis.get.return_value = None

            with patch('call_service.main.SessionLocal') as mock_session:
                mock_db = MagicMock()
                mock_session.return_value = mock_db
                mock_db.query.return_value.filter.return_value.all.return_value = []

                response = call_client.get("/history/1")

                # Проверяем, что использовался правильный ключ
                mock_redis.get.assert_called_with("history:1")
