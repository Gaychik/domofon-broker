from fastapi import FastAPI, Request
import logging
from datetime import datetime, timezone

# ИСПРАВЛЕНИЕ #8: Добавлен формат с timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
    
app = FastAPI(title="Logging Service")

# ИСПРАВЛЕНИЕ #8: Хранилище логов
logs_store: list = []

#Логирование событий
@app.post("/log")
async def log_event(request: Request):
  
    data = await request.json()
    data["timestamp"] = datetime.now(timezone.utc).isoformat()  # ИСПРАВЛЕНИЕ #8
    logger.info(f"EVENT: {data}")
    logs_store.append(data)
    
    return {"status": "logged"}


#Отправка уведомлений (Observer pattern)
# ПРОБЛЕМА: Этот эндпоинт существует, но никто его не вызывает
@app.post("/notification")
async def send_notification(request: Request):

    data = await request.json()
    data["timestamp"] = datetime.now(timezone.utc).isoformat()  # ИСПРАВЛЕНИЕ #8
    logger.info(f"NOTIFICATION: {data}")
    logs_store.append({"type": "notification", **data})
    
    return {"status": "notified"}


# ИСПРАВЛЕНИЕ: Эндпоинт для получения логов
@app.get("/logs")
async def get_logs():
    return logs_store