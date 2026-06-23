import pytest
from fastapi.testclient import TestClient
import sys
import os


os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["PROVIDER_URL"] = "http://localhost:8003"
os.environ["CALL_SERVICE_URL"] = "http://localhost:8002"
os.environ["LOGGING_SERVICE_URL"] = "http://localhost:8004"
os.environ["USER_SERVICE_URL"] = "http://localhost:8001"
os.environ["JWT_SECRET_KEY"] = "testsecretkey"
os.environ["JWT_ALGORITHM"] = "HS256"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api_gateway'))


@pytest.fixture
def gateway_client():
    from api_gateway.main import app
    return TestClient(app)


@pytest.fixture
def user_client():
    from user_service.main import app
    return TestClient(app)


@pytest.fixture
def call_client():
    from call_service.main import app
    return TestClient(app)
