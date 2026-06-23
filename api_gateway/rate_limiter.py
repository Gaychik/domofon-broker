from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # ОШИБКА: функция не реализована
        # ↓ ↓ ↓
        # ФИКС: причина: функция не реализована, отсутствует счёт запросов
        # ФИКС: Реализовал функцию, добавил счётчик запросов по IP
        current_time = time.time()

        client_ip = request.client.host

        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if current_time - t < 1
        ]

        if len(self.requests[client_ip]) >= 10:
            raise HTTPException(
                status_code=429,
                detail="Слишком много запросов"
            )

        self.requests[client_ip].append(current_time)

        # ОШИБКА: rate limiter не подключён к middleware
        # ↓ ↓ ↓
        # ФИКС: подключил в api_gateway\main.py

rate_limiter = RateLimiter()
