import pytest
import os
import sys

# Set test environment BEFORE importing any service modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["JWT_SECRET_KEY"] = "supersecretkeychangeinproduction"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["LOGGING_SERVICE_URL"] = "http://localhost:8004"
os.environ["PROVIDER_URL"] = "http://localhost:8003"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Добавляем директории каждого сервиса в sys.path для локальных импортов
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _svc in ("api_gateway", "user_service", "call_service", "logging_service", "call_provider"):
    sys.path.insert(0, os.path.join(_root, _svc))

import jwt as pyjwt
from unittest.mock import patch, MagicMock

JWT_SECRET = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = os.environ["JWT_ALGORITHM"]

# Mock Redis globally before any module imports
_mock_redis = MagicMock()
_mock_redis.get.return_value = None

_redis_patch = patch("redis.from_url", return_value=_mock_redis)
_redis_patch.start()


@pytest.fixture
def gateway_client():
    #Фикстура для тестирования API Gateway
    from api_gateway.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def user_client():
    #Фикстура для тестирования User Service
    from user_service.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def call_client():
    #Фикстура для тестирования Call Service
    from call_service.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def auth_token():
    """Создаёт валидный JWT токен для тестов"""
    from datetime import datetime, timedelta
    payload = {
        "user_id": 1,
        "username": "admin",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow()
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@pytest.fixture
def auth_headers(auth_token):
    """Заголовки с авторизацией для тестов"""
    return {"Authorization": f"Bearer {auth_token}"}
