from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # Проверяет, не превысил ли IP лимит запросов в минуту.
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Удаляет устаревшие записи (старше 60 секунд)
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if now - timestamp < 60
        ]
        # Если запросов больше лимита — выбрасывает 429
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
        # Добавляем текущий запрос
        self.requests[client_ip].append(now)

rate_limiter = RateLimiter(requests_per_minute=10)
