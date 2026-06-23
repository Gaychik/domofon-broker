from fastapi.testclient import TestClient
from api_gateway.main import app

client = TestClient(app)

# Тест успешной аутентификации и выдачи JWT токена
def test_login_success_returns_jwt():
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

# Тест отказа в аутентификации при неверном пароле
def test_login_wrong_password_returns_401():
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"}
    )

    assert response.status_code == 401

# Тест запрета доступа без JWT токена
def test_protected_route_without_token_returns_401():
    response = client.get("/users/1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

# Тест запрета доступа при передаче некорректного JWT токена
def test_protected_route_with_invalid_token_returns_401():
    response = client.get(
        "/users/1",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401