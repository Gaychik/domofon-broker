from unittest.mock import AsyncMock, MagicMock, patch


class TestCallService:
    def test_save_call_to_database(self, call_client):
        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db

            mock_post = AsyncMock()
            with (
                patch("httpx.AsyncClient") as mock_http,
                patch("main.redis_client"),
            ):
                mock_http.return_value.__aenter__.return_value.post = mock_post

                resp = call_client.post(
                    "/call/callback",
                    json={"user_id": 1, "status": "answered"},
                )

        assert resp.status_code == 200
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_initiate_call_success(self, call_client):
        """Провайдер ответил — возвращаем статус."""
        mock_post = AsyncMock(
            return_value=MagicMock(json=MagicMock(return_value={"status": "answered"}))
        )

        with patch("httpx.AsyncClient") as mock_http:
            mock_http.return_value.__aenter__.return_value.post = mock_post
            resp = call_client.post("/call/initiate", json={"user_id": 1})

        assert resp.status_code == 200
        assert resp.json()["call_status"] == "answered"

    def test_initiate_call_provider_fails(self, call_client):
        """Провайдер недоступен — failed."""
        bad_client = MagicMock()
        bad_client.post = AsyncMock(side_effect=Exception)
        good_client = MagicMock()
        good_client.post = AsyncMock()

        with patch("httpx.AsyncClient") as mock_http:
            mock_http.return_value.__aenter__.side_effect = [bad_client, good_client]
            resp = call_client.post("/call/initiate", json={"user_id": 1})

        assert resp.status_code == 200
        assert resp.json()["call_status"] == "failed"

    def test_redis_cache_used(self, call_client):
        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db
            db.query.return_value.filter.return_value.all.return_value = []

            with patch("main.redis_client") as redis_mock:
                redis_mock.get.return_value = None
                call_client.get("/history/1")
                redis_mock.get.assert_called_with("history:1")

    def test_redis_cache_hit(self, call_client):
        """При попадании в кэш — БД не дёргается."""
        import json

        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db

            with patch("main.redis_client") as redis_mock:
                redis_mock.get.return_value = json.dumps(
                    [
                        {
                            "id": 1,
                            "status": "answered",
                            "created_at": "2024-01-01T00:00:00",
                        }
                    ]
                )
                resp = call_client.get("/history/1")

        assert resp.status_code == 200
        assert resp.json()[0]["status"] == "answered"
        db.query.assert_not_called()
