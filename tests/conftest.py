import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")


def _get_app(service_dir):
    sys.path.insert(0, os.path.join(ROOT, service_dir))
    for mod in ("main", "models", "rate_limiter"):
        sys.modules.pop(mod, None)
    import main  # type: ignore

    return main.app


@pytest.fixture
def gateway_client():
    return TestClient(_get_app("api_gateway"))


@pytest.fixture
def user_client():
    return TestClient(_get_app("user_service"))


@pytest.fixture
def call_client():
    return TestClient(_get_app("call_service"))
