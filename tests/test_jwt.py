import pytest
from api_gateway.jwt_auth import create_token, verify_token, SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime, timedelta, timezone

class TestJWTAuth:
    
    def test_jwt_token_creation(self):
        #Тест создания JWT токена
        # Этот тест нужно будет реализовать после добавления JWT
        token = create_token(username="admin", user_id=1)
        assert isinstance(token, str)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["username"] == "admin"
        assert payload["user_id"] == 1
        assert "exp" in payload
    
    def test_jwt_token_validation(self):
        #Тест валидации JWT токена
        token = create_token(username="test", user_id=5)
        payload = verify_token(token)
        assert payload["username"] == "test"
    
    def test_token_expiration(self):
        #Тест истечения срока действия токена
        payload = {
            "user_id": 1,
            "username": "expired",
            "iat": datetime.now(timezone.utc) - timedelta(hours=1),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(ValueError, match="Token expired"):
            verify_token(token)