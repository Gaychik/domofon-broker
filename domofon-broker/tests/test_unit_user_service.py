import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestUserService:

    def test_create_user_success(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.filter.return_value.first.return_value = None

            def refresh_side_effect(obj):
                obj.id = 1
                obj.phone = "+79991234567"
                obj.name = "John"

            mock_db.refresh.side_effect = refresh_side_effect

            with patch('user_service.main.log_event', new_callable=AsyncMock):
                response = user_client.post("/users", json={"phone": "+79991234567", "name": "John"})

            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == "+79991234567"
            assert data["name"] == "John"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()

    def test_create_user_duplicate_phone(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_existing = MagicMock()
            mock_existing.phone = "+79991234567"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

            response = user_client.post("/users", json={"phone": "+79991234567", "name": "Jane"})

            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

    def test_get_user_found(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.phone = "+79991234567"
            mock_user.name = "John"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            with patch('user_service.main.log_event', new_callable=AsyncMock):
                response = user_client.get("/users/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["phone"] == "+79991234567"

    def test_get_user_not_found(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.filter.return_value.first.return_value = None

            response = user_client.get("/users/999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_create_user_logs_event(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.filter.return_value.first.return_value = None

            def refresh_side_effect(obj):
                obj.id = 1

            mock_db.refresh.side_effect = refresh_side_effect

            with patch('user_service.main.log_event', new_callable=AsyncMock) as mock_log:
                response = user_client.post("/users", json={"phone": "+79990000000", "name": "Test"})
                mock_log.assert_called_once()
                call_args = mock_log.call_args
                assert call_args[0][0] == "user_created"
