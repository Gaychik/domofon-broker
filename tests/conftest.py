import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Переопределяем DATABASE_URL для локального тестирования (используем localhost, т.к. порт проброшен)
os.environ["DATABASE_URL"] = "postgresql://domofon:domofon123@localhost:5432/domofon"

# Теперь импорты приложений будут использовать этот URL
import pytest
from fastapi.testclient import TestClient

# Фикстура для user_service
@pytest.fixture(scope="module")
def user_client():
    from user_service.main import app
    return TestClient(app)

# Фикстура для call_service
@pytest.fixture(scope="module")
def call_client():
    from call_service.main import app
    return TestClient(app)