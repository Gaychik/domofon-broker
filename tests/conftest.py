"""Shared fixtures for all tests."""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import httpx

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure api_gateway/ is on sys.path so `import jwt_auth` works inside api_gateway.main
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_gateway"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_jwt_token():
    """Generate a valid JWT token for testing."""
    from api_gateway.jwt_auth import create_token
    return create_token(user_id=1, username="admin")


# ---------------------------------------------------------------------------
# Fixtures – use httpx.AsyncClient with ASGITransport (Python 3.14 safe)
# ---------------------------------------------------------------------------
@pytest.fixture
def gateway_client():
    """API Gateway async test client."""
    from api_gateway.main import app, _request_log
    _request_log.clear()
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    yield client
    _request_log.clear()


@pytest.fixture
def user_client():
    """User Service async test client backed by in-memory SQLite."""
    mock_pg_engine = MagicMock()
    with patch("sqlalchemy.create_engine", return_value=mock_pg_engine):
        import user_service.main as us

    engine = create_engine("sqlite:///:memory:")
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    us.engine = engine
    us.SessionLocal = TestSession
    us.Base.metadata.create_all(bind=engine)

    transport = httpx.ASGITransport(app=us.app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    yield client


@pytest.fixture
def call_client():
    """Call Service async test client backed by in-memory SQLite + mocked Redis."""
    mock_pg_engine = MagicMock()
    with patch("sqlalchemy.create_engine", return_value=mock_pg_engine):
        import call_service.main as cs

    engine = create_engine("sqlite:///:memory:")
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    mock_redis = MagicMock()
    mock_redis.get.return_value = None

    cs.engine = engine
    cs.SessionLocal = TestSession
    cs.redis_client = mock_redis
    cs.Base.metadata.create_all(bind=engine)

    transport = httpx.ASGITransport(app=cs.app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    yield client


@pytest.fixture
def call_provider_client():
    """Call Provider async test client."""
    from call_provider.main import app
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    yield client


@pytest.fixture
def auth_headers():
    """Valid JWT Authorization headers."""
    token = _get_jwt_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Clear rate-limiting state before and after every test."""
    try:
        from api_gateway.main import _request_log
        _request_log.clear()
    except ImportError:
        pass
    yield
    try:
        from api_gateway.main import _request_log
        _request_log.clear()
    except ImportError:
        pass


@pytest.fixture
def anyio_backend():
    """Force trio backend for async tests (Python 3.14 asyncio workaround)."""
    return "trio"
