from fastapi import Request, HTTPException
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        # Словарь: IP -> список временных меток запросов
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # Получаем IP клиента
        client_ip = request.client.host
        now = time.time()
        window_start = now - 1  # ✅ Окно — 1 секунда (вместо 60)
        
        # Удаляем старые записи (старше 1 секунды)
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > window_start
        ]
        
        # Проверяем, не превышен ли лимит
        if len(self.requests[client_ip]) >= self.requests_per_second:
            raise HTTPException(
                status_code=429,
                detail=f"Too Many Requests. Limit: {self.requests_per_second} req/sec"
            )
        
        # Добавляем текущий запрос в список
        self.requests[client_ip].append(now)


# Создаём экземпляр rate limiter
rate_limiter = RateLimiter(requests_per_second=10)