import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUserService:
    #Тест создания пользователя
    def test_create_user(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            created_user = MagicMock()
            created_user.id = 1
            created_user.phone = "+79991234567"
            created_user.name = "Test"
            mock_db.refresh.side_effect = lambda u: setattr(u, 'id', 1) or None

            with patch('user_service.main.httpx.AsyncClient') as mock_http:
                mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock(post=AsyncMock()))
                mock_http.return_value.__aexit__ = AsyncMock(return_value=False)

                response = user_client.post("/users?phone=%2B79991234567&name=Test")

                assert response.status_code == 200
                mock_db.commit.assert_called_once()

    # FIX #1: Тест отправки события в Logging Service
    def test_create_user_logs_to_logging_service(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.refresh.side_effect = lambda u: setattr(u, 'id', 1) or None

            mock_post = AsyncMock()
            mock_http_instance = MagicMock()
            mock_http_instance.post = mock_post
            mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
            mock_http_instance.__aexit__ = AsyncMock(return_value=False)

            with patch('user_service.main.httpx.AsyncClient', return_value=mock_http_instance):
                response = user_client.post("/users?phone=%2B79991234567&name=Test")
                assert response.status_code == 200
                # После FIX #1 — вызов httpx.post к logging_service должен быть
                mock_post.assert_called_once()
                call_url = mock_post.call_args[0][0]
                assert "/log" in call_url

    # FIX #7: Тест проверки уникальности телефона
    def test_create_user_duplicate_phone_rejected(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            # Пользователь с таким телефоном уже существует
            existing = MagicMock()
            existing.id = 1
            existing.phone = "+79991234567"
            mock_db.query.return_value.filter.return_value.first.return_value = existing

            response = user_client.post("/users?phone=%2B79991234567&name=New")

            # Должен вернуть 400 (дубликат телефона)
            assert response.status_code == 400
            assert "already registered" in response.json()["detail"]

    #Тест получения пользователя
    def test_get_user(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            user = MagicMock()
            user.id = 1
            user.phone = "+79991234567"
            user.name = "Test"
            mock_db.query.return_value.filter.return_value.first.return_value = user

            response = user_client.get("/users/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1

    def test_get_user_not_found(self, user_client):
        with patch('user_service.main.SessionLocal') as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            response = user_client.get("/users/999")

            assert response.status_code == 404
