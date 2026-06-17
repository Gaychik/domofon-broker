import pytest
import httpx

@pytest.mark.asyncio
async def test_full_call_flow():
    async with httpx.AsyncClient() as client:
        # 1. Получаем токен
        login_resp = await client.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Создаём пользователя
        user_resp = await client.post(
            "http://localhost:8000/users",
            json={"phone": "+79991112233", "name": "Integration Test"},
            headers=headers
        )
        assert user_resp.status_code == 200
        user_id = user_resp.json()["id"]

        # 3. Совершаем звонок
        call_resp = await client.post(
            "http://localhost:8000/call/initiate",
            json={"user_id": user_id},
            headers=headers
        )
        assert call_resp.status_code == 200
        assert call_resp.json()["status"] == "answered"

        # 4. Проверяем историю
        history_resp = await client.get(
            f"http://localhost:8000/history/{user_id}",
            headers=headers
        )
        assert history_resp.status_code == 200
        assert len(history_resp.json()) > 0


@pytest.mark.asyncio
async def test_rate_limiting():
    async with httpx.AsyncClient() as client:
        # Получаем токен
        login_resp = await client.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создаём пользователя для теста
        user_resp = await client.post(
            "http://localhost:8000/users",
            json={"phone": "+79990000001", "name": "RateTest"},
            headers=headers
        )
        assert user_resp.status_code == 200
        user_id = user_resp.json()["id"]

        # Отправляем 20 запросов
        statuses = []
        for _ in range(20):
            resp = await client.get(
                f"http://localhost:8000/users/{user_id}",
                headers=headers
            )
            statuses.append(resp.status_code)

        # Проверяем, что есть 429
        assert 429 in statuses, f"Rate limiting not working, statuses: {statuses}"

        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]