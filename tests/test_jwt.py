"""Tests for JWT authentication module (Problem 10)."""
import pytest
import jwt
import time
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_gateway"))

from jwt_auth import create_token, verify_token, SECRET_KEY, ALGORITHM


class TestJWT:
    """Tests for JWT token creation, verification, and expiration."""

    def test_create_token_returns_string(self):
        """create_token returns a non-empty string."""
        token = create_token(user_id=1, username="admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Valid token decodes to correct payload."""
        token = create_token(user_id=42, username="testuser")
        payload = verify_token(token)
        assert payload["user_id"] == 42
        assert payload["username"] == "testuser"

    def test_token_contains_required_fields(self):
        """Token payload includes user_id, username, exp, iat."""
        token = create_token(user_id=1, username="admin")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "user_id" in payload
        assert "username" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_token_expires_in_30_minutes(self):
        """Token expires approximately 30 minutes after creation."""
        token = create_token(user_id=1, username="admin")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.utcfromtimestamp(payload["exp"])
        iat = datetime.utcfromtimestamp(payload["iat"])
        delta = exp - iat
        assert 29 <= delta.total_seconds() / 60 <= 31

    def test_expired_token_raises_error(self):
        """Expired token raises ExpiredSignatureError."""
        expired_payload = {
            "user_id": 1,
            "username": "admin",
            "exp": datetime.utcnow() - timedelta(minutes=1),
            "iat": datetime.utcnow() - timedelta(minutes=31),
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(expired_token)

    def test_invalid_token_raises_error(self):
        """Tampered token raises InvalidTokenError."""
        with pytest.raises(jwt.InvalidTokenError):
            verify_token("not.a.valid.token")

    def test_wrong_secret_raises_error(self):
        """Token signed with wrong secret raises InvalidSignatureError."""
        payload = {
            "user_id": 1,
            "username": "admin",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, "wrong_secret", algorithm=ALGORITHM)

        with pytest.raises(jwt.InvalidTokenError):
            verify_token(token)
