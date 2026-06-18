import pytest
from unittest.mock import patch, MagicMock


class TestUserService:

    def test_create_user_success(self, user_client):
        """Fix #7: успешное создание пользователя"""
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            with patch('httpx.AsyncClient'):
                response = user_client.post("/users", json={"phone": "+79991234567", "name": "Test"})
            assert response.status_code == 200

    def test_create_user_duplicate_phone(self, user_client):
        """Fix #7: дубликат телефона возвращает 400"""
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
            response = user_client.post("/users", json={"phone": "+79991234567", "name": "Dup"})
            assert response.status_code == 400
            assert "Phone already exists" in response.json()["detail"]

    def test_get_user_not_found(self, user_client):
        """пользователь не найден — 404"""
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            response = user_client.get("/users/999")
            assert response.status_code == 404

    def test_logging_called_on_create(self, user_client):
        """Fix #1: при создании вызывается Logging Service"""
        with patch('user_service.main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            with patch('httpx.AsyncClient') as mock_http:
                mock_post = MagicMock()
                mock_http.return_value.__aenter__.return_value.post = mock_post
                user_client.post("/users", json={"phone": "+79991111111", "name": "Log"})
                mock_post.assert_called_once()
                assert "/log" in mock_post.call_args[0][0]
