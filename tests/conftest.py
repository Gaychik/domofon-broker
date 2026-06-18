import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DATABASE_URL to SQLite so services don't need PostgreSQL
os.environ["DATABASE_URL"] = "sqlite:///test.db"

# Mock redis.from_url before importing any service that uses it
import redis
_real_redis_from_url = redis.from_url
redis.from_url = MagicMock(return_value=MagicMock())

# Now import service apps — they will use SQLite + mocked Redis
from user_service.main import app as user_app
from call_service.main import app as call_app
from api_gateway.main import app as gateway_app


@pytest.fixture
def gateway_client():
    return TestClient(gateway_app)


@pytest.fixture
def user_client():
    return TestClient(user_app)


@pytest.fixture
def call_client():
    return TestClient(call_app)
