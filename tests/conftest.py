import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import sys
import os

# Устанавливаем SQLite для тестов ДО импорта сервисов
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_test_engine():
    """Создаёт in-memory SQLite engine с общим соединением (StaticPool)"""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def gateway_client():
    """Фикстура для тестирования API Gateway"""
    from api_gateway.main import app
    return TestClient(app)


@pytest.fixture
def user_client():
    """Фикстура для тестирования User Service"""
    with patch('user_service.main.httpx.AsyncClient'):
        import user_service.main as user_mod
        user_mod.engine = _make_test_engine()
        user_mod.SessionLocal = __import__('sqlalchemy.orm', fromlist=['sessionmaker']).sessionmaker(
            autocommit=False, autoflush=False, bind=user_mod.engine)
        user_mod.Base.metadata.create_all(bind=user_mod.engine)
        yield TestClient(user_mod.app)


@pytest.fixture
def call_client():
    """Фикстура для тестирования Call Service с мокнутым Redis"""
    with patch('call_service.main.redis_client') as mock_redis, \
         patch('call_service.main.httpx.AsyncClient'):
        import call_service.main as call_mod
        call_mod.engine = _make_test_engine()
        call_mod.SessionLocal = __import__('sqlalchemy.orm', fromlist=['sessionmaker']).sessionmaker(
            autocommit=False, autoflush=False, bind=call_mod.engine)
        call_mod.Base.metadata.create_all(bind=call_mod.engine)
        yield TestClient(call_mod.app), mock_redis


@pytest.fixture
def jwt_token():
    """Фикстура: создаёт валидный JWT токен для тестов"""
    from api_gateway.jwt_auth import create_token
    return create_token(username="admin", user_id=1)


@pytest.fixture
def auth_headers(jwt_token):
    """Фикстура: заголовки авторизации для тестов"""
    return {"Authorization": f"Bearer {jwt_token}"}
