"""Unit tests for Call Service (Problems 2, 4, 6)."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.anyio
class TestCallService:
    """Tests for call persistence, Redis caching, and observer notifications."""

    # ── Problem 2: Save to DB ──

    async def test_save_call_to_database(self, call_client):
        """Call is saved to PostgreSQL after initiation (Problem 2)."""
        with patch("call_service.main.httpx.AsyncClient") as mock_http, \
             patch("call_service.main.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "answered"}
            mock_client.post.return_value = mock_response

            response = await call_client.post(
                "/call/initiate",
                json={"user_id": 1},
            )

            assert response.status_code == 200
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    # ── Problem 4: Redis cache keys ──

    async def test_redis_cache_key_includes_user_id(self, call_client):
        """Redis cache key includes user_id (Problem 4)."""
        with patch("call_service.main.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.all.return_value = []

            with patch("call_service.main.redis_client") as mock_redis:
                mock_redis.get.return_value = None

                await call_client.get("/history/42")

                mock_redis.get.assert_called_with("history:42")

    async def test_redis_cache_hit(self, call_client):
        """History returned from Redis cache when available."""
        import json

        cached_data = json.dumps([{"id": 1, "status": "answered", "created_at": "2024-01-01T00:00:00"}])

        with patch("call_service.main.redis_client") as mock_redis:
            mock_redis.get.return_value = cached_data

            response = await call_client.get("/history/1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "answered"

    # ── Problem 6: Observer notification ──

    async def test_call_notification_sent(self, call_client):
        """Notification sent to logging service after call (Problem 6)."""
        with patch("call_service.main.httpx.AsyncClient") as mock_http, \
             patch("call_service.main.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "answered"}
            mock_client.post.return_value = mock_response

            await call_client.post("/call/initiate", json={"user_id": 1})

            notification_calls = [
                c for c in mock_client.post.call_args_list
                if "/notification" in str(c)
            ]
            assert len(notification_calls) > 0, "No notification sent to logging service"

    async def test_call_log_sent(self, call_client):
        """Log event sent to logging service after call (Problem 6)."""
        with patch("call_service.main.httpx.AsyncClient") as mock_http, \
             patch("call_service.main.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "answered"}
            mock_client.post.return_value = mock_response

            await call_client.post("/call/initiate", json={"user_id": 1})

            log_calls = [
                c for c in mock_client.post.call_args_list
                if "/log" in str(c)
            ]
            assert len(log_calls) > 0, "No log event sent to logging service"

    # ── Edge cases ──

    async def test_call_provider_failure_returns_failed(self, call_client):
        """Returns 'failed' status when provider is unreachable."""
        with patch("call_service.main.httpx.AsyncClient") as mock_http, \
             patch("call_service.main.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Connection refused")

            response = await call_client.post("/call/initiate", json={"user_id": 1})

            assert response.status_code == 200
            assert response.json()["status"] == "failed"
            mock_db.commit.assert_called_once()

    async def test_history_empty(self, call_client):
        """Returns empty list when no calls exist."""
        with patch("call_service.main.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.all.return_value = []

            with patch("call_service.main.redis_client") as mock_redis:
                mock_redis.get.return_value = None

                response = await call_client.get("/history/999")

                assert response.status_code == 200
                assert response.json() == []
