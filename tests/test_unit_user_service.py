import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def gateway_client():
    #Фикстура для тестирования API Gateway
    from api_gateway.main import app
    return TestClient(app)

@pytest.fixture
def user_client():
    #Фикстура для тестирования User Service
    from user_service.main import app
    return TestClient(app)

@pytest.fixture
def call_client():
    #Фикстура для тестирования Call Service
    from call_service.main import app
    return TestClient(app)