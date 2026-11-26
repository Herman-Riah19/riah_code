# apps/modules/shared/decorators/retry.py
"""Retry and circuit breaker decorators."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from apps.modules.shared.kernel.exceptions import RiahAppError

P = ParamSpec("P")
R = TypeVar("R")


def retryable(
    maxAttempts: int = 3,
    baseDelay: float = 1.0,
    maxDelay: float = 60.0,
    exponentialBase: float = 2.0,
    jitter: bool = True,
    retryableExceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a callable with exponential backoff."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            lastException: Exception | None = None

            for attempt in range(maxAttempts):
                try:
                    return func(*args, **kwargs)
                except retryableExceptions as error:
                    lastException = error
                    if attempt == maxAttempts - 1:
                        break

                    delay = min(baseDelay * (exponentialBase**attempt), maxDelay)
                    if jitter:
                        delay *= 0.5 + random.random()

                    time.sleep(delay)

            if lastException is None:  # pragma: no cover - defensive branch
                raise RuntimeError("Retryable callable produced no exception")
            raise lastException

        return wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker state machine."""

    def __init__(
        self,
        failureThreshold: int = 5,
        recoveryTimeout: float = 30.0,
        expectedException: type[Exception] = Exception,
    ) -> None:
        self.failureThreshold = failureThreshold
        self.recoveryTimeout = recoveryTimeout
        self.expectedException = expectedException
        self.failureCount = 0
        self.lastFailureTime: float | None = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Run the callable unless the breaker is open."""
        if self.state == "open":
            lastFailure = self.lastFailureTime
            if lastFailure is not None and time.time() - lastFailure > self.recoveryTimeout:
                self.state = "half-open"
            else:
                raise RiahAppError("Circuit breaker ouvert", details={"state": self.state})

        try:
            result = func(*args, **kwargs)
        except self.expectedException:
            self._onFailure()
            raise
        self._onSuccess()
        return result

    def _onSuccess(self) -> None:
        self.failureCount = 0
        self.state = "closed"

    def _onFailure(self) -> None:
        self.failureCount += 1
        self.lastFailureTime = time.time()
        if self.failureCount >= self.failureThreshold:
            self.state = "open"


def circuitBreaker(
    failureThreshold: int = 5,
    recoveryTimeout: float = 30.0,
    expectedException: type[Exception] = Exception,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a callable with a shared circuit breaker."""
    breaker = CircuitBreaker(failureThreshold, recoveryTimeout, expectedException)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
