import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestCallService:

    def test_save_call_to_database(self, call_client):
        with patch('call_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            def refresh_side_effect(obj):
                obj.id = 1

            mock_db.refresh.side_effect = refresh_side_effect

            with patch('httpx.AsyncClient') as mock_http:
                mock_response = MagicMock()
                mock_response.json.return_value = {"status": "answered"}
                mock_http.return_value.__aenter__.return_value.post.return_value = mock_response

                with patch('call_service.main.log_event', new_callable=AsyncMock):
                    with patch('call_service.main.redis_client') as mock_redis:
                        response = call_client.post("/call/initiate", json={"user_id": 1})

                assert mock_db.commit.call_count >= 1

    def test_redis_cache_used(self, call_client):
        with patch('call_service.main.redis_client') as mock_redis:
            mock_redis.get.return_value = None

            with patch('call_service.main.SessionLocal') as mock_session:
                mock_db = MagicMock()
                mock_session.return_value = mock_db
                mock_db.query.return_value.filter.return_value.all.return_value = []

                response = call_client.get("/history/1")

                mock_redis.get.assert_called_with("history:1")

    def test_redis_cache_hit(self, call_client):
        with patch('call_service.main.redis_client') as mock_redis:
            cached_data = json.dumps([{"id": 1, "status": "answered", "created_at": "2024-01-01T00:00:00"}])
            mock_redis.get.return_value = cached_data

            response = call_client.get("/history/1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "answered"

    def test_call_callback(self, call_client):
        with patch('call_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_call = MagicMock()
            mock_call.id = 1
            mock_call.user_id = 1
            mock_call.status = "initiated"
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_call

            with patch('call_service.main.log_event', new_callable=AsyncMock):
                with patch('call_service.main.redis_client') as mock_redis:
                    response = call_client.post("/call/callback", json={"user_id": 1, "status": "answered"})

            assert response.status_code == 200
            mock_db.commit.assert_called_once()

    def test_initiate_call_invalidate_cache(self, call_client):
        with patch('call_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            def refresh_side_effect(obj):
                obj.id = 1

            mock_db.refresh.side_effect = refresh_side_effect

            with patch('httpx.AsyncClient') as mock_http:
                mock_response = MagicMock()
                mock_response.json.return_value = {"status": "answered"}
                mock_http.return_value.__aenter__.return_value.post.return_value = mock_response

                with patch('call_service.main.log_event', new_callable=AsyncMock):
                    with patch('call_service.main.redis_client') as mock_redis:
                        response = call_client.post("/call/initiate", json={"user_id": 1})

                        mock_redis.delete.assert_called_with("history:1")
