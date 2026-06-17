import asyncio
import time

import httpx
import pytest


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_call_flow(self):
        """Сквозной тест: создание пользователя → звонок → история"""
        phone = f"+7999{int(time.time())}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:8000/users",
                json={"phone": phone, "name": "Integration Test"},
            )
            assert resp.status_code == 200
            user_id = resp.json()["id"]
            assert resp.json()["phone"] == phone
            assert resp.json()["name"] == "Integration Test"

            resp = await client.post(
                "http://localhost:8000/call/initiate",
                headers={"X-User-Token": "test"},
                json={"user_id": user_id},
            )
            assert resp.status_code == 200
            assert resp.json()["user_id"] == user_id
            assert resp.json()["call_status"] in {"answered", "busy", "no_answer"}

            await asyncio.sleep(2)

            resp = await client.get(
                f"http://localhost:8000/history/{user_id}",
                headers={"X-User-Token": "test"},
            )
            assert resp.status_code == 200
            assert len(resp.json()) > 0, resp.text
            assert resp.json()[0]["status"] in {"answered", "busy", "no_answer"}

    @pytest.mark.asyncio
    async def test_auth_required(self):
        """Без X-User-Token защищённые эндпоинты возвращают 401"""
        async with httpx.AsyncClient() as client:
            assert (
                await client.get("http://localhost:8000/users/1")
            ).status_code == 401
            assert (
                await client.get("http://localhost:8000/history/1")
            ).status_code == 401
            assert (
                await client.post(
                    "http://localhost:8000/call/initiate", json={"user_id": 1}
                )
            ).status_code == 401

    @pytest.mark.asyncio
    async def test_get_user(self):
        """Получение созданного пользователя."""
        phone = f"+7998{int(time.time())}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:8000/users",
                json={"phone": phone, "name": "Get Test"},
            )
            assert resp.status_code == 200
            user_id = resp.json()["id"]

            resp = await client.get(
                f"http://localhost:8000/users/{user_id}",
                headers={"X-User-Token": "test"},
            )
            assert resp.status_code == 200
            assert resp.json()["phone"] == phone

    @pytest.mark.asyncio
    async def test_z_rate_limiting(self):
        """После 60 запросов должен быть 429"""
        async with httpx.AsyncClient() as client:
            codes = []
            for _ in range(65):
                resp = await client.get(
                    "http://localhost:8000/users/1",
                    headers={"X-User-Token": "test"},
                )
                codes.append(resp.status_code)
            assert 429 in codes
