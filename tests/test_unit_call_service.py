import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCallService:
    # FIX #2: Тест сохранения звонка в БД
    def test_save_call_to_database(self, call_client):
        with patch('call_service.main.SessionLocal') as mock_session_cls, \
             patch('call_service.main.redis_client') as mock_redis:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_redis.get.return_value = None

            saved_call = MagicMock()
            saved_call.id = 1
            saved_call.status = "answered"
            saved_call.user_id = 1
            mock_db.refresh.side_effect = lambda c: None

            mock_http_instance = MagicMock()
            mock_http_instance.post = AsyncMock(return_value=MagicMock(
                json=MagicMock(return_value={"status": "answered"})
            ))
            mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
            mock_http_instance.__aexit__ = AsyncMock(return_value=False)

            with patch('call_service.main.httpx.AsyncClient', return_value=mock_http_instance):
                response = call_client.post("/call/initiate", params={"user_id": 1})

                # FIX #2: commit вызывается — звонок сохраняется в БД
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()

    # FIX #4: Тест использования правильного ключа Redis кэша
    def test_redis_cache_key_includes_user_id(self, call_client):
        with patch('call_service.main.redis_client') as mock_redis, \
             patch('call_service.main.SessionLocal') as mock_session_cls:
            mock_redis.get.return_value = None
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_db.query.return_value.filter.return_value.all.return_value = []

            response = call_client.get("/history/1")

            # FIX #4: Ключ кэша должен включать user_id
            mock_redis.get.assert_called_with("history:1")
            mock_redis.setex.assert_called_once()
            write_key = mock_redis.setex.call_args[0][0]
            assert write_key == "history:1", f"Expected 'history:1', got '{write_key}'"

    # FIX #4: Тест попадания в кэш
    def test_redis_cache_hit(self, call_client):
        with patch('call_service.main.redis_client') as mock_redis:
            cached_data = json.dumps([{"id": 1, "status": "answered", "created_at": "2024-01-01T00:00:00"}])
            mock_redis.get.return_value = cached_data

            response = call_client.get("/history/1")

            assert response.status_code == 200

    # FIX #6: Тест отправки уведомления (Observer pattern)
    def test_observer_notification_sent(self, call_client):
        with patch('call_service.main.SessionLocal') as mock_session_cls, \
             patch('call_service.main.redis_client'):
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_db.refresh.side_effect = lambda c: None

            calls = []

            async def mock_post(url, **kwargs):
                calls.append(url)
                return MagicMock(json=MagicMock(return_value={"status": "answered"}))

            mock_http_instance = MagicMock()
            mock_http_instance.post = mock_post
            mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
            mock_http_instance.__aexit__ = AsyncMock(return_value=False)

            with patch('call_service.main.httpx.AsyncClient', return_value=mock_http_instance):
                response = call_client.post("/call/initiate", params={"user_id": 1})

                # FIX #6: Уведомление в logging_service/notification
                notification_calls = [u for u in calls if "notification" in u]
                assert len(notification_calls) > 0, "Observer notification should be sent"
