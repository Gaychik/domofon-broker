import pytest
import httpx
import asyncio
import uuid


class TestIntegration:
    """Интеграционные тесты — требуют запущенного docker-compose"""

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_full_call_flow(self):
        """Сквозной тест: создание пользователя -> звонок -> история"""
        # Уникальный телефон, чтобы избежать конфликтов между запусками
        unique_phone = f"+7999{uuid.uuid4().hex[:7]}"
        async with httpx.AsyncClient() as client:
            token = await self._get_token(client)
            headers = {"Authorization": f"Bearer {token}"}

            user_response = await client.post(
                "http://localhost:8000/users",
                json={"phone": unique_phone, "name": "Integration Test"},
                headers=headers
            )
            assert user_response.status_code == 200, user_response.text
            user_id = user_response.json().get("id")

            call_response = await client.post(
                "http://localhost:8000/call/initiate",
                json={"user_id": user_id},
                headers=headers
            )
            assert call_response.status_code == 200

            history_response = await client.get(
                f"http://localhost:8000/history/{user_id}", headers=headers
            )
            assert len(history_response.json()) > 0

    @pytest.mark.asyncio
    async def test_duplicate_phone_rejected(self):
        """Проблема #7: Два пользователя с одинаковым телефоном"""
        async with httpx.AsyncClient() as client:
            token = await self._get_token(client)
            headers = {"Authorization": f"Bearer {token}"}

            await client.post(
                "http://localhost:8000/users",
                json={"phone": "+79990001111", "name": "User1"},
                headers=headers
            )
            response = await client.post(
                "http://localhost:8000/users",
                json={"phone": "+79990001111", "name": "User2"},
                headers=headers
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Проблема #9: Rate limiting"""
        async with httpx.AsyncClient() as client:
            token = await self._get_token(client)
            headers = {"Authorization": f"Bearer {token}"}
            responses = []
            for i in range(20):
                response = await client.get(
                    "http://localhost:8000/users/1", headers=headers
                )
                responses.append(response)
            status_codes = [r.status_code for r in responses]
            assert 429 in status_codes

    @pytest.mark.asyncio
    async def test_auth_required(self):
        """Проблема #5: Запросы без токена отклоняются"""
        # Ждём, чтобы окно rate limiter (1 сек) истекло после предыдущих тестов
        await asyncio.sleep(1.1)
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/users/1")
            assert response.status_code == 401
