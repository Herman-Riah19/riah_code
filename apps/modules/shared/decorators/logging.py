# apps/modules/shared/decorators/logging.py
"""Logging decorators"""
import time
import logging
from functools import wraps
from flask import request, g
from apps.modules.shared.config import settings

logger = logging.getLogger(__name__)


def logExecution(logArgs: bool = False, logResult: bool = False, logLevel: int = logging.INFO):
    """Decorator to log function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            funcName = f"{func.__module__}.{func.__qualname__}"
            startTime = time.perf_counter()
            
            extra = {
                "function": funcName,
                "args": str(args) if logArgs else None,
                "kwargs": str(kwargs) if logArgs else None,
            }
            
            logger.log(logLevel, f"Executing {funcName}", extra=extra)
            
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - startTime
                
                extra["durationMs"] = round(duration * 1000, 2)
                if logResult:
                    extra["result"] = str(result)[:500]
                
                logger.log(logLevel, f"Completed {funcName}", extra=extra)
                return result
            except Exception as e:
                duration = time.perf_counter() - startTime
                extra["durationMs"] = round(duration * 1000, 2)
                extra["error"] = str(e)
                logger.exception(f"Failed {funcName}", extra=extra)
                raise
        return wrapper
    return decorator


def logErrors(func):
    """Decorator to log exceptions with context"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                f"Error in {func.__qualname__}",
                extra={
                    "function": f"{func.__module__}.{func.__qualname__}",
                    "error": str(e),
                    "errorType": type(e).__name__,
                }
            )
            raise
    return wrapper


def logRequest(func):
    """Decorator to log HTTP request details (Flask)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.debug:
            return func(*args, **kwargs)
        
        startTime = time.perf_counter()
        
        logger.info(
            f"HTTP {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remoteAddr": request.remote_addr,
                "userAgent": request.headers.get("User-Agent"),
                "userId": getattr(g, "currentUser", None) and g.currentUser.id,
            }
        )
        
        try:
            response = func(*args, **kwargs)
            duration = time.perf_counter() - startTime
            
            statusCode = response[1] if isinstance(response, tuple) else 200
            logger.info(
                f"HTTP {request.method} {request.path} -> {statusCode}",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "statusCode": statusCode,
                    "durationMs": round(duration * 1000, 2),
                }
            )
            return response
        except Exception as e:
            duration = time.perf_counter() - startTime
            logger.error(
                f"HTTP {request.method} {request.path} -> ERROR",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "error": str(e),
                    "durationMs": round(duration * 1000, 2),
                },
                exc_info=True
            )
            raise
    return wrapper