from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # FIX #9: Реализована проверка количества запросов от одного IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Удаляем устаревшие записи
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < self.window_seconds
        ]
        
        # Проверяем лимит
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Too many requests")
        
        self.requests[client_ip].append(now)

# Rate limiter: 10 запросов в секунду
rate_limiter = RateLimiter(max_requests=10, window_seconds=1)
