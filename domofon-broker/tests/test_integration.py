import pytest
import httpx
import jwt
from datetime import datetime, timedelta
import os


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeychangeinproduction")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def generate_token():
    payload = {
        "user_id": 1,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


class TestIntegration:

    @pytest.mark.asyncio
    async def test_full_call_flow(self):
        token = generate_token()
        headers = {"X-User-Token": token}

        async with httpx.AsyncClient() as client:
            user_response = await client.post(
                "http://localhost:8000/users",
                json={"phone": "+79991112233", "name": "Integration Test"},
                headers=headers
            )

            if user_response.status_code == 200:
                user_id = user_response.json().get("id")

                call_response = await client.post(
                    "http://localhost:8000/call/initiate",
                    json={"user_id": user_id},
                    headers=headers
                )

                history_response = await client.get(
                    f"http://localhost:8000/history/{user_id}",
                    headers=headers
                )

                assert len(history_response.json()) > 0

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        token = generate_token()
        headers = {"X-User-Token": token}

        async with httpx.AsyncClient() as client:
            responses = []
            for i in range(20):
                response = await client.get(
                    "http://localhost:8000/users/1",
                    headers=headers
                )
                responses.append(response)

            status_codes = [r.status_code for r in responses]
            assert 429 in status_codes
