# apps/modules/shared/decorators/rateLimit.py
"""Rate limiting decorator"""
import time
from functools import wraps
from collections import defaultdict
from flask import request, jsonify
from apps.modules.shared.kernel.exceptions import RiahAppError
from apps.modules.shared.config import settings


class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
    
    def isAllowed(self, key: str, maxRequests: int, windowSeconds: int) -> tuple[bool, dict]:
        now = time.time()
        windowStart = now - windowSeconds
        
        # Clean old entries
        self._requests[key] = [ts for ts in self._requests[key] if ts > windowStart]
        
        currentCount = len(self._requests[key])
        
        if currentCount >= maxRequests:
            oldest = self._requests[key][0] if self._requests[key] else now
            retryAfter = int(oldest + windowSeconds - now) + 1
            return False, {
                "allowed": False,
                "current": currentCount,
                "limit": maxRequests,
                "retryAfter": retryAfter,
            }
        
        self._requests[key].append(now)
        return True, {
            "allowed": True,
            "current": currentCount + 1,
            "limit": maxRequests,
            "remaining": maxRequests - currentCount - 1,
        }


_rateLimiter = RateLimiter()


def rateLimited(
    maxRequests: int | None = None,
    windowSeconds: int | None = None,
    keyFunc: callable | None = None,
):
    """Decorator for rate limiting endpoints"""
    maxReq = maxRequests or settings.rateLimitRequests
    window = windowSeconds or settings.rateLimitWindow
    
    def defaultKeyFunc():
        user = getattr(request, "currentUser", None)
        if user:
            return f"user:{user.id}"
        return f"ip:{request.remote_addr}"
    
    getKey = keyFunc or defaultKeyFunc
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = getKey()
            allowed, info = _rateLimiter.isAllowed(key, maxReq, window)
            
            # Add rate limit headers
            response = func(*args, **kwargs)
            
            # Handle both direct return and tuple (response, status)
            if isinstance(response, tuple):
                resp, status = response[0], response[1]
            else:
                resp, status = response, 200
            
            if hasattr(resp, "headers"):
                resp.headers["X-RateLimit-Limit"] = str(info["limit"])
                resp.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
                resp.headers["X-RateLimit-Reset"] = str(int(time.time() + window))
            
            if not allowed:
                if hasattr(resp, "headers"):
                    resp.headers["Retry-After"] = str(info["retryAfter"])
                raise RiahAppError(
                    "Trop de requêtes",
                    details=info,
                ).with_status(429)
            
            return response
        return wrapper
    return decorator