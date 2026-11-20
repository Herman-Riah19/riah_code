# apps/modules/shared/decorators/retry.py
"""Retry and circuit breaker decorators"""
import time
import random
from functools import wraps
from typing import Callable, Type, Tuple
from apps.modules.shared.kernel.exceptions import RiahAppError


def retryable(
    maxAttempts: int = 3,
    baseDelay: float = 1.0,
    maxDelay: float = 60.0,
    exponentialBase: float = 2.0,
    jitter: bool = True,
    retryableExceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            lastException = None
            
            for attempt in range(maxAttempts):
                try:
                    return func(*args, **kwargs)
                except retryableExceptions as e:
                    lastException = e
                    if attempt == maxAttempts - 1:
                        break
                    
                    delay = min(baseDelay * (exponentialBase ** attempt), maxDelay)
                    if jitter:
                        delay *= (0.5 + random.random())  # 0.5-1.5x
                    
                    time.sleep(delay)
            
            raise lastException
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    def __init__(
        self,
        failureThreshold: int = 5,
        recoveryTimeout: float = 30.0,
        expectedException: Type[Exception] = Exception,
    ):
        self.failureThreshold = failureThreshold
        self.recoveryTimeout = recoveryTimeout
        self.expectedException = expectedException
        self.failureCount = 0
        self.lastFailureTime: float | None = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.lastFailureTime > self.recoveryTimeout:
                self.state = "half-open"
            else:
                raise RiahAppError("Circuit breaker ouvert", details={"state": self.state})
        
        try:
            result = func(*args, **kwargs)
            self._onSuccess()
            return result
        except self.expectedException as e:
            self._onFailure()
            raise
    
    def _onSuccess(self):
        self.failureCount = 0
        self.state = "closed"
    
    def _onFailure(self):
        self.failureCount += 1
        self.lastFailureTime = time.time()
        if self.failureCount >= self.failureThreshold:
            self.state = "open"


def circuitBreaker(
    failureThreshold: int = 5,
    recoveryTimeout: float = 30.0,
    expectedException: Type[Exception] = Exception,
):
    """Decorator for circuit breaker pattern"""
    breaker = CircuitBreaker(failureThreshold, recoveryTimeout, expectedException)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator