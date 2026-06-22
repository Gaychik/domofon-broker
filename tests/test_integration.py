import pytest
import httpx

class TestIntegration:

    @pytest.mark.asyncio
    async def test_full_call_flow(self):
        #Сквозной тест: создание пользователя -> звонок -> история

        async with httpx.AsyncClient(trust_env=False) as client:
            # Получаем токен для авторизации
            login_resp = await client.post(
                "http://localhost:8000/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            assert login_resp.status_code == 200
            token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Создаем пользователя
            user_response = await client.post(
                "http://localhost:8000/users",
                json={"phone": "+79991112233", "name": "Integration Test"},
                headers=headers
            )

            # Этот тест покажет все проблемы системы
            if user_response.status_code == 200:
                user_id = user_response.json().get("id")

                # 2. Совершаем звонок
                call_response = await client.post(
                    "http://localhost:8000/call/initiate",
                    json={"user_id": user_id},
                    headers=headers
                )

                # 3. Получаем историю
                history_response = await client.get(
                    f"http://localhost:8000/history/{user_id}",
                    headers=headers
                )

                # Ожидаем, что история не пуста
                assert len(history_response.json()) > 0

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        #Тест rate limiting
        async with httpx.AsyncClient(trust_env=False) as client:

            # логин
            login_resp = await client.post(
                "http://localhost:8000/api/auth/login",
                json={
                    "username": "admin",
                    "password": "admin123"
                }
            )

            assert login_resp.status_code == 200

            token = login_resp.json()["access_token"]

            headers = {
                "Authorization": f"Bearer {token}"
            }

            responses = []

            # делаем много запросов подряд
            for i in range(65):
                response = await client.get(
                    "http://localhost:8000/users/1",
                    headers=headers
                )
                responses.append(response)

            status_codes = [r.status_code for r in responses]

            # хотя бы один должен получить 429
            assert 429 in status_codes
