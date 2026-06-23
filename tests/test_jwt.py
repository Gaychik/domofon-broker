import pytest
import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from api_gateway.jwt_auth import create_token, verify_token

class TestJWTAuth:
    
    def test_jwt_token_creation(self):
        #Тест создания JWT токена
        token = create_token(user_id=1, username="admin")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_token_validation(self):
        #Тест валидации JWT токена
        token = create_token(user_id=1, username="admin")
        payload = verify_token(token)

        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert "iat" in payload
        assert "exp" in payload
    
    def test_token_expiration(self):
        #Тест истечения срока действия токена
        token = create_token(user_id=1, username="admin")
        payload = verify_token(token)

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        lifetime_seconds = (exp - iat).total_seconds()

        assert lifetime_seconds == 30 * 60