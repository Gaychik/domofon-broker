from unittest.mock import MagicMock, patch


class TestUserService:
    def test_create_user(self, user_client):
        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db
            db.execute.return_value.scalar.return_value = None

            with patch("httpx.AsyncClient"):
                resp = user_client.post(
                    "/users", json={"phone": "+79991234567", "name": "John"}
                )

        assert resp.status_code == 200
        assert resp.json()["phone"] == "+79991234567"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_duplicate_phone(self, user_client):
        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db
            db.execute.return_value.scalar.return_value = object()

            resp = user_client.post(
                "/users", json={"phone": "+79991234567", "name": "John"}
            )

        assert resp.status_code == 409

    def test_get_user(self, user_client):
        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db

            user = MagicMock()
            user.id = 1
            user.phone = "+79991234567"
            user.name = "John"
            db.query.return_value.filter.return_value.first.return_value = user

            resp = user_client.get("/users/1")

        assert resp.status_code == 200
        assert resp.json() == {"id": 1, "phone": "+79991234567", "name": "John"}

    def test_user_not_found(self, user_client):
        with patch("main.SessionLocal") as mock_sess:
            db = MagicMock()
            mock_sess.return_value = db
            db.query.return_value.filter.return_value.first.return_value = None

            resp = user_client.get("/users/999")

        assert resp.status_code == 404
