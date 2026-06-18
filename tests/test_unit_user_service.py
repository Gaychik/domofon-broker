"""Unit tests for User Service (Problems 1 & 7)."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.anyio
class TestUserService:
    """Tests for user creation, phone uniqueness, and logging."""

    # ── Problem 7: Phone uniqueness ──

    async def test_create_user_success(self, user_client):
        """Successful user creation returns 200 with correct data."""
        with patch("user_service.main.httpx.AsyncClient") as mock_http:
            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            response = await user_client.post(
                "/users",
                json={"phone": "+79991234567", "name": "Иван Петров"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == "+79991234567"
            assert data["name"] == "Иван Петров"
            assert "id" in data

    async def test_phone_uniqueness_check(self, user_client):
        """Cannot create two users with the same phone number (Problem 7)."""
        with patch("user_service.main.httpx.AsyncClient") as mock_http:
            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            await user_client.post(
                "/users",
                json={"phone": "+79991111111", "name": "User1"},
            )
            response = await user_client.post(
                "/users",
                json={"phone": "+79991111111", "name": "User2"},
            )

            assert response.status_code == 400
            assert "already exists" in response.json()["detail"].lower() or \
                   "Phone" in response.json()["detail"]

    # ── Problem 1: Logging ──

    async def test_create_user_sends_log(self, user_client):
        """POST /users sends event to logging service (Problem 1)."""
        with patch("user_service.main.httpx.AsyncClient") as mock_http:
            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            await user_client.post(
                "/users",
                json={"phone": "+79992223344", "name": "Test"},
            )

            log_calls = [
                c for c in mock_client.post.call_args_list
                if "/log" in str(c)
            ]
            assert len(log_calls) > 0, "No log event sent to logging service"

    # ── GET /users ──

    async def test_get_user_success(self, user_client):
        """Can retrieve an existing user."""
        with patch("user_service.main.httpx.AsyncClient") as mock_http:
            mock_client = MagicMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            create_resp = await user_client.post(
                "/users",
                json={"phone": "+79995556677", "name": "Test"},
            )
            user_id = create_resp.json()["id"]

            response = await user_client.get(f"/users/{user_id}")
            assert response.status_code == 200
            assert response.json()["phone"] == "+79995556677"

    async def test_get_user_not_found(self, user_client):
        """Returns 404 for non-existent user."""
        response = await user_client.get("/users/9999")
        assert response.status_code == 404
