import pytest
import httpx

class TestIntegration:
    
    @pytest.mark.asyncio
    async def test_full_call_flow(self):
        #Сквозной тест: создание пользователя -> звонок -> история
        
        async with httpx.AsyncClient() as client:
            # 1. Создаем пользователя
            user_response = await client.post(
                "http://localhost:8000/users",
                json={"phone": "+79991112233", "name": "Integration Test"}
            )
            
            # Этот тест покажет все проблемы системы
            if user_response.status_code == 200:
                user_id = user_response.json().get("id")
                
                # 2. Совершаем звонок
                call_response = await client.post(
                    "http://localhost:8000/call/initiate",
                    json={"user_id": user_id}
                )
                
                # 3. Получаем историю
                history_response = await client.get(f"http://localhost:8000/history/{user_id}")
                
                # Ожидаем, что история не пуста
                assert len(history_response.json()) > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        #Тест rate limiting
        async with httpx.AsyncClient() as client:
            #Получение JWT
            login_response = await client.post(
                "http://localhost:8000/api/auth/login",
                json={
                    "username": "admin",
                    "password": "admin123"
                }
            )

            token = login_response.json()["access_token"]

            headers = {
                "Authorization": f"Bearer {token}"
            }

            # Отправляем 20 запросов подряд
            responses = []
            for i in range(20):
                response = await client.get("http://localhost:8000/users/1", headers=headers)
                responses.append(response)
            
            # Некоторые запросы должны получить 429 Too Many Requests
            status_codes = [r.status_code for r in responses]
            assert 429 in status_codes