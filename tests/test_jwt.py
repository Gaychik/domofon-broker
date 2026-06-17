import pytest
import jwt
from datetime import datetime, timedelta

class TestJWTAuth:
    
    def test_jwt_token_creation(self):

        from api_gateway.jwt_auth import create_token

        token = create_token({"user_id": 1, "username": "admin"})

        assert token is not None
    
    def test_jwt_token_validation(self):

        from api_gateway.jwt_auth import (
            create_token,
            verify_token
        )

        token = create_token({"user_id": 1, "username": "admin"})

        payload = verify_token(token)

        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
    
    def test_token_expiration(self):

        token = jwt.encode(
            {
                "user_id": 1,
                "exp": datetime.utcnow() - timedelta(seconds=1)
            },
            "super_secret_key",
            algorithm="HS256"
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                "super_secret_key",
                algorithms=["HS256"]
            )

    