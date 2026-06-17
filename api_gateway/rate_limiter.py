import time as time_module
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def check_rate_limit(self, request: Request):
        ip = request.client.host if request.client else None

        if not ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Какая-то невозможная ситуация с отсутствием IP",
            )
        now = time_module.time()
        window = now - 60
        self.requests[ip] = [time for time in self.requests[ip] if time > window]

        self.requests[ip].append(now)

        if len(self.requests[ip]) > self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много запросов!",
            )


rate_limiter = RateLimiter()
