from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.client_requests = defaultdict(list)

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        now = time.time()
        self.client_requests[client_ip] = [t for t in self.client_requests[client_ip] if now - t < 1]
        if len(self.client_requests[client_ip]) >= self.requests_per_second:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        self.client_requests[client_ip].append(now)

rate_limiter = RateLimiter()