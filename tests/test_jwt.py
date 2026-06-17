from unittest.mock import MagicMock, patch


class TestAuth:
    def test_no_token_returns_401(self, gateway_client):
        resp = gateway_client.get("/users/1")
        assert resp.status_code == 401

    def test_call_initiate_no_token_401(self, gateway_client):
        resp = gateway_client.post("/call/initiate", json={"user_id": 1})
        assert resp.status_code == 401

    def test_history_no_token_401(self, gateway_client):
        resp = gateway_client.get("/history/1")
        assert resp.status_code == 401

    def test_valid_token_passes(self, gateway_client):
        with patch("httpx.AsyncClient") as mock_http:
            mock_http.return_value.__aenter__.return_value.get.return_value = MagicMock(
                json=MagicMock(
                    return_value={"id": 1, "phone": "+79991234567", "name": "John"}
                )
            )
            resp = gateway_client.get("/users/1", headers={"X-User-Token": "test"})

        assert resp.status_code == 200

    def test_empty_token_401(self, gateway_client):
        resp = gateway_client.get("/users/1", headers={"X-User-Token": ""})
        assert resp.status_code == 401

    def test_create_user_open(self, gateway_client):
        with patch("httpx.AsyncClient") as mock_http:
            mock_http.return_value.__aenter__.return_value.post.return_value = (
                MagicMock(
                    json=MagicMock(
                        return_value={"id": 1, "phone": "+79991234567", "name": "John"}
                    )
                )
            )
            resp = gateway_client.post(
                "/users", json={"phone": "+79991234567", "name": "John"}
            )
        assert resp.status_code == 200
