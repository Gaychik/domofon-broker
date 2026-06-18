from fastapi import FastAPI, Request
import logging
from datetime import datetime

# Формат логов с timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
    
app = FastAPI(title="Logging Service")

#Логирование событий
@app.post("/log")
async def log_event(request: Request):
  
    data = await request.json()
    data["timestamp"] = datetime.utcnow().isoformat()  # Fix #8
    logger.info(f"EVENT: {data}")
    
    return {"status": "logged"}


#Отправка уведомлений (Observer pattern)
# ПРОБЛЕМА: Этот эндпоинт существует, но никто его не вызывает
@app.post("/notification")
async def send_notification(request: Request):

    data = await request.json()
    data["timestamp"] = datetime.utcnow().isoformat()  # Fix #8
    logger.info(f"NOTIFICATION: {data}")
    
    return {"status": "notified"}