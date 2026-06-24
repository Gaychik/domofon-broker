from fastapi import FastAPI, Request
import logging
from datetime import datetime

# ✅ ИСПРАВЛЕНО: Настроен формат логов с timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Logging Service")


# Логирование событий
@app.post("/log")
async def log_event(request: Request):
    data = await request.json()
    
    # ✅ Добавляем timestamp в сами данные для полноты
    data_with_timestamp = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }
    
    logger.info(f"EVENT: {data_with_timestamp}")
    
    return {"status": "logged"}


# Отправка уведомлений (Observer pattern)
@app.post("/notification")
async def send_notification(request: Request):
    data = await request.json()
    
    # ✅ Добавляем timestamp в уведомления
    data_with_timestamp = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }
    
    logger.info(f"NOTIFICATION: {data_with_timestamp}")
    
    return {"status": "notified"}