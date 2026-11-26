# apps/modules/shared/decorators/rateLimit.py
"""In-memory rate limiting decorator."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import request

from apps.modules.shared.config import settings
from apps.modules.shared.kernel.exceptions import RateLimitError

KeyFunction = Callable[[], str]
ViewFunction = Callable[..., Any]


class RateLimiter:
    """Sliding-window counter kept in memory (use Redis in production)."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    def isAllowed(
        self,
        key: str,
        maxRequests: int,
        windowSeconds: int,
    ) -> tuple[bool, dict[str, Any]]:
        """Record one request and report whether it is allowed."""
        now = time.time()
        windowStart = now - windowSeconds

        self._requests[key] = [
            timestamp for timestamp in self._requests[key] if timestamp > windowStart
        ]
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
    keyFunc: KeyFunction | None = None,
) -> Callable[[ViewFunction], ViewFunction]:
    """Reject requests that exceed the configured sliding window."""
    maxReq = maxRequests or settings.rateLimitRequests
    window = windowSeconds or settings.rateLimitWindow

    def defaultKeyFunc() -> str:
        user = getattr(request, "currentUser", None)
        if user:
            return f"user:{user.id}"
        return f"ip:{request.remote_addr}"

    getKey = keyFunc or defaultKeyFunc

    def decorator(func: ViewFunction) -> ViewFunction:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = getKey()
            allowed, info = _rateLimiter.isAllowed(key, maxReq, window)
            if not allowed:
                raise RateLimitError("Trop de requetes", details=info)

            response = func(*args, **kwargs)

            # Handle both a direct response and a `(response, status)` tuple.
            resp = response[0] if isinstance(response, tuple) else response
            if hasattr(resp, "headers"):
                resp.headers["X-RateLimit-Limit"] = str(info["limit"])
                resp.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
                resp.headers["X-RateLimit-Reset"] = str(int(time.time() + window))

            return response

        return wrapper

    return decorator
