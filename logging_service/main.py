from fastapi import FastAPI, Request
import logging
from datetime import datetime

# ПРОБЛЕМА: Формат логов 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
app = FastAPI(title="Logging Service")

#Логирование событий
# FIX #8: Добавлен timestamp в логи
@app.post("/log")
async def log_event(request: Request):
  
    data = await request.json()
    
    # FIX #8: Добавляем timestamp к данным
    data["timestamp"] = datetime.utcnow().isoformat()

    logger.info(f"EVENT: {data}")
    
    return {"status": "logged"}


#Отправка уведомлений (Observer pattern)
# FIX #8: Добавлен timestamp в уведомления
@app.post("/notification")
async def send_notification(request: Request):

    data = await request.json()
    
    # FIX #8: Добавляем timestamp
    data["timestamp"] = datetime.utcnow().isoformat()
    
    logger.info(f"NOTIFICATION: {data}")
    
    return {"status": "notified"}