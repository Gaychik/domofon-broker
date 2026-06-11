from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # ОШИБКА: функция не реализована
        # TODO: Реализовать проверку количества запросов от одного IP
        # Если превышено - выбрасывать HTTPException(status_code=429)
        pass

# ОШИБКА: rate limiter не подключён к middleware
rate_limiter = RateLimiter()
