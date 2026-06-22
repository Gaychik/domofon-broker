import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

class TestCallService:
    #Тест сохранения звонка в БД
    def test_save_call_to_database(self, call_client):
        with patch('main.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            
            with patch('httpx.AsyncClient') as mock_http, \
                 patch('main.redis_client') as mock_redis:
                mock_response = MagicMock()
                mock_response.json.return_value = {"status": "answered"}
                mock_http.return_value.__aenter__.return_value.post.return_value = mock_response
                
                response = call_client.post("/call/callback", json={"user_id": 1, "status": "answered"})  # ИЗМЕНЕНО: добавлен status
                
                # Проверяем, что был вызов commit (сохранение в БД)
                assert response.status_code == 200
                assert response.json()["status"] == "answered"
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
    
    #Тест использования Redis кэша
    def test_redis_cache_used(self, call_client):
        with patch("main.redis_client") as redis_mock:
            redis_mock.get.return_value = json.dumps([{"id": 1, "status": "answered", "created_at": "2024-01-01T00:00:00"}])
            response = call_client.get("/history/1")
            assert response.status_code == 200
            redis_mock.get.assert_called_with("history:1")