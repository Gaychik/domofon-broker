"""Integration tests – API Gateway with mocked downstream services.

Tests cover: JWT auth (Problem 5/10), rate limiting (Problem 9),
phone uniqueness (Problem 7), full call flow (Problems 2/3/4/6).
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.anyio
class TestIntegration:
    """End-to-end tests through the API Gateway."""

    # ── JWT Authentication (Problems 5 & 10) ──

    async def test_no_auth_returns_401(self, gateway_client):
        """Request without Authorization header returns 401."""
        response = await gateway_client.post(
            "/users",
            json={"phone": "+79991234567", "name": "Test"},
        )
        assert response.status_code == 401

    async def test_invalid_auth_returns_401(self, gateway_client):
        """Request with bad token returns 401."""
        response = await gateway_client.post(
            "/users",
            json={"phone": "+79991234567", "name": "Test"},
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    async def test_login_returns_jwt(self, gateway_client):
        """POST /api/auth/login returns a valid JWT token."""
        response = await gateway_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_credentials(self, gateway_client):
        """Wrong credentials return 401."""
        response = await gateway_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401

    # ── Rate Limiting (Problem 9) ──

    async def test_rate_limiting(self, gateway_client, auth_headers):
        """More than 10 requests per second triggers 429."""
        with patch("api_gateway.main.httpx.AsyncClient") as mock_http:
            mock_client = AsyncMock()
            mock_http.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1, "phone": "+7", "name": "X"}
            mock_client.get.return_value = mock_response

            responses = []
            for _ in range(20):
                r = await gateway_client.get("/users/1", headers=auth_headers)
                responses.append(r.status_code)

            assert 429 in responses, "Rate limiting not working – no 429 in 20 rapid requests"

    # ── User Creation via Gateway ──

    async def test_create_user_via_gateway(self, gateway_client, auth_headers):
        """Full user creation flow through API Gateway."""
        with patch("api_gateway.main.httpx.AsyncClient") as mock_http:
            mock_client = AsyncMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": 1,
                "phone": "+79991234567",
                "name": "Иван Петров",
            }
            mock_client.post.return_value = mock_response

            response = await gateway_client.post(
                "/users",
                json={"phone": "+79991234567", "name": "Иван Петров"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            assert response.json()["id"] == 1

    # ── Phone Uniqueness via Gateway (Problem 7) ──

    async def test_duplicate_phone_returns_400(self, gateway_client, auth_headers):
        """Duplicate phone number returns 400 through gateway."""
        with patch("api_gateway.main.httpx.AsyncClient") as mock_http:
            mock_client = AsyncMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            mock_ok = MagicMock()
            mock_ok.status_code = 200
            mock_ok.json.return_value = {"id": 1, "phone": "+79990000000", "name": "User1"}

            mock_dup = MagicMock()
            mock_dup.status_code = 400
            mock_dup.json.return_value = {"detail": "Phone number already exists"}

            mock_client.post.side_effect = [mock_ok, mock_dup]

            await gateway_client.post(
                "/users",
                json={"phone": "+79990000000", "name": "User1"},
                headers=auth_headers,
            )
            response = await gateway_client.post(
                "/users",
                json={"phone": "+79990000000", "name": "User2"},
                headers=auth_headers,
            )

            assert response.status_code == 400

    # ── Call Flow via Gateway ──

    async def test_call_initiate_via_gateway(self, gateway_client, auth_headers):
        """Call initiation through API Gateway."""
        with patch("api_gateway.main.httpx.AsyncClient") as mock_http:
            mock_client = AsyncMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "answered", "user_id": 1}
            mock_client.post.return_value = mock_response

            response = await gateway_client.post(
                "/call/initiate",
                json={"user_id": 1},
                headers=auth_headers,
            )

            assert response.status_code == 200
            assert response.json()["status"] == "answered"

    async def test_history_via_gateway(self, gateway_client, auth_headers):
        """Get history through API Gateway."""
        with patch("api_gateway.main.httpx.AsyncClient") as mock_http:
            mock_client = AsyncMock()
            mock_http.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": 1, "status": "answered", "created_at": "2024-01-01T00:00:00"}
            ]
            mock_client.get.return_value = mock_response

            response = await gateway_client.get("/history/1", headers=auth_headers)

            assert response.status_code == 200
            assert len(response.json()) > 0
