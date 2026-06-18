from fastapi import FastAPI, Request
import logging
from datetime import datetime, timezone

# Problem 8: Формат логов включает timestamp
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Logging Service")


@app.post("/log")
async def log_event(request: Request):
    """Логирование событий с timestamp."""
    data = await request.json()

    # Problem 8: Добавляем timestamp к данным лога
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    logger.info(f"EVENT: {data}")

    return {"status": "logged"}


@app.post("/notification")
async def send_notification(request: Request):
    """Отправка уведомлений (Observer pattern)."""
    data = await request.json()

    # Добавляем timestamp
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    logger.info(f"NOTIFICATION: {data}")

    return {"status": "notified"}
