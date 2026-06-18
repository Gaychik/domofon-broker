import pytest
import jwt
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class TestJWTAuth:
    
    def test_jwt_token_creation(self):
        # FIX #10: Тест создания JWT токена
        from api_gateway.jwt_auth import create_token
        
        token = create_token(user_id=1, username="admin")
        
        assert token is not None
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_jwt_token_validation(self):
        # FIX #10: Тест валидации JWT токена
        from api_gateway.jwt_auth import create_token, verify_token
        
        token = create_token(user_id=1, username="admin")
        payload = verify_token(token)
        
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
    
    def test_token_expiration(self):
        # FIX #10: Тест истечения срока действия токена
        from fastapi import HTTPException
        from api_gateway.jwt_auth import verify_token
        
        # Создаём просроченный токен
        expired_payload = {
            "user_id": 1,
            "username": "admin",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        
        assert exc_info.value.status_code == 401
    
    def test_invalid_token_rejected(self):
        # FIX #10: Тест отклонения невалидного токена
        from fastapi import HTTPException
        from api_gateway.jwt_auth import verify_token
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_token_expiry_is_30_minutes(self):
        # FIX #10: Токен должен истекать через 30 минут
        from api_gateway.jwt_auth import create_token
        
        token = create_token(user_id=1, username="admin")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        exp_minus_iat = payload["exp"] - payload["iat"]
        assert exp_minus_iat == 1800, f"Token should expire in 30 min (1800s), got {exp_minus_iat}s"
