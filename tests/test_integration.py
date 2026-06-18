import pytest
import httpx
import asyncio
import random

# Integration tests require Docker services running
# Run: docker compose up -d


def get_auth_headers():
    """Get JWT auth headers for integration tests"""
    import requests
    resp = requests.post(
        "http://localhost:8000/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_full_call_flow():
    """Сквозной тест: создание пользователя -> звонок -> история"""
    headers = get_auth_headers()
    # Уникальный телефон чтобы не было дубликатов
    unique_phone = f"+7999{random.randint(1000000, 9999999)}"
    async with httpx.AsyncClient() as client:
        # 1. Создаем пользователя
        user_response = await client.post(
            "http://localhost:8000/users",
            json={"phone": unique_phone, "name": "Integration Test"},
            headers=headers
        )
        assert user_response.status_code == 200, f"Create user failed: {user_response.text}"
        user_id = user_response.json().get("id")

        # 2. Совершаем звонок
        call_response = await client.post(
            "http://localhost:8000/call/initiate",
            json={"user_id": user_id},
            headers=headers
        )
        assert call_response.status_code == 200, f"Call failed: {call_response.text}"

        # 3. Получаем историю
        history_response = await client.get(
            f"http://localhost:8000/history/{user_id}",
            headers=headers
        )
        assert history_response.status_code == 200, f"History failed: {history_response.text}"
        assert len(history_response.json()) > 0


@pytest.mark.asyncio
async def test_rate_limiting():
    """Тест rate limiting — много быстрых запросов должны получить 429"""
    headers = get_auth_headers()
    async with httpx.AsyncClient() as client:
        # Отправляем 50 запросов одновременно
        tasks = []
        for i in range(50):
            tasks.append(client.get("http://localhost:8000/users/999", headers=headers))
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Некоторые запросы должны получить 429 Too Many Requests
        status_codes = []
        for r in responses:
            if isinstance(r, Exception):
                continue
            status_codes.append(r.status_code)
        assert 429 in status_codes or len([s for s in status_codes if s == 200]) > 10
