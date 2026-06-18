from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        # Sliding window — не больше 10 запросов в секунду
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 1  
        max_requests = 10  
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < window
        ]
        self.requests[client_ip].append(now)
        if len(self.requests[client_ip]) > max_requests:
            raise HTTPException(status_code=429, detail="Too Many Requests")

# Rate limiter: sliding window — 10 запросов в секунду на IP, при превышении HTTPException 429
rate_limiter = RateLimiter()
