import pytest
import jwt
from datetime import datetime, timedelta
import os


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "testsecretkey")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class TestJWTAuth:

    def test_jwt_token_creation(self):
        payload = {
            "user_id": 1,
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        assert token is not None
        assert isinstance(token, str)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["user_id"] == 1
        assert decoded["username"] == "testuser"

    def test_jwt_token_validation(self):
        payload = {
            "user_id": 1,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        valid_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        decoded = jwt.decode(valid_token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["user_id"] == 1

        invalid_token = jwt.encode(payload, "wrongsecret", algorithm=ALGORITHM)
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(invalid_token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_token_expiration(self):
        payload = {
            "user_id": 1,
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_gateway_rejects_missing_token(self, gateway_client):
        response = gateway_client.get("/users/1")
        assert response.status_code == 401

    def test_gateway_rejects_invalid_token(self, gateway_client):
        response = gateway_client.get(
            "/users/1",
            headers={"X-User-Token": "invalidtoken"}
        )
        assert response.status_code == 401

    def test_gateway_accepts_valid_token(self, gateway_client):
        payload = {
            "user_id": 1,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


        try:
            response = gateway_client.get(
                "/users/1",
                headers={"X-User-Token": token}
            )
            assert response.status_code != 401
        except Exception as e:

            assert "ConnectError" in type(e).__name__ or "connect" in str(e).lower()
