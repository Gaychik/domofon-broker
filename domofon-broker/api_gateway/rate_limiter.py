from fastapi import Request
from fastapi.responses import JSONResponse
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()


        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < 60
        ]


        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )


        self.requests[client_ip].append(now)
        return None


rate_limiter = RateLimiter()
