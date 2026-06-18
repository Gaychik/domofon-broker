from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # ИСПРАВЛЕНИЕ #9: Реализована проверка количества запросов от одного IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # Удаляем запросы старше 1 секунды
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 1.0]
        if len(self.requests[client_ip]) >= self.requests_per_second:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        self.requests[client_ip].append(now)

# ОШИБКА: rate limiter не подключён к middleware
rate_limiter = RateLimiter()
