import logging
from fastapi.testclient import TestClient
from logging_service.main import app

client = TestClient(app)

# Тест автоматического добавления timestamp в событие логирования
def test_log_event_adds_timestamp(caplog):
    with caplog.at_level(logging.INFO):
        response = client.post("/log", json={"event": "test_event"})

    assert response.status_code == 200
    assert response.json()["status"] == "logged"
    assert "timestamp" in caplog.text

# Тест автоматического добавления timestamp в уведомление
def test_notification_adds_timestamp(caplog):
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/notification",
            json={"event": "call", "status": "answered"}
        )

    assert response.status_code == 200
    assert response.json()["status"] == "notified"
    assert "timestamp" in caplog.text
    assert "NOTIFICATION" in caplog.text