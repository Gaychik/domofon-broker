import pytest
from fastapi.testclient import TestClient
import sys
import os

os.environ["DATABASE_URL"] = "postgresql://domofon:domofon123@localhost:5432/domofon"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def gateway_client():
    #Фикстура для тестирования API Gateway
    from api_gateway.main import app
    return TestClient(app)

@pytest.fixture
def user_client():
    #Фикстура для тестирования User Service"""
    from user_service.main import app
    return TestClient(app)

@pytest.fixture
def call_client():
    #Фикстура для тестирования Call Service
    from call_service.main import app
    return TestClient(app)