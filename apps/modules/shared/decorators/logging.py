# apps/modules/shared/decorators/logging.py
"""Logging decorators."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import g, request

from apps.modules.shared.config import settings

logger = logging.getLogger(__name__)

ViewFunction = Callable[..., Any]


def logExecution(
    logArgs: bool = False,
    logResult: bool = False,
    logLevel: int = logging.INFO,
) -> Callable[[ViewFunction], ViewFunction]:
    """Log the start, duration and outcome of one callable."""

    def decorator(func: ViewFunction) -> ViewFunction:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            funcName = f"{func.__module__}.{func.__qualname__}"
            startTime = time.perf_counter()

            extra: dict[str, Any] = {
                "function": funcName,
                "callArgs": str(args) if logArgs else None,
                "callKwargs": str(kwargs) if logArgs else None,
            }

            logger.log(logLevel, f"Executing {funcName}", extra=extra)

            try:
                result = func(*args, **kwargs)
            except Exception as error:
                extra["durationMs"] = round((time.perf_counter() - startTime) * 1000, 2)
                extra["error"] = str(error)
                logger.exception(f"Failed {funcName}", extra=extra)
                raise

            extra["durationMs"] = round((time.perf_counter() - startTime) * 1000, 2)
            if logResult:
                extra["result"] = str(result)[:500]

            logger.log(logLevel, f"Completed {funcName}", extra=extra)
            return result

        return wrapper

    return decorator


def logErrors(func: ViewFunction) -> ViewFunction:
    """Log any exception with its function context, then re-raise it."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as error:
            logger.exception(
                f"Error in {func.__qualname__}",
                extra={
                    "function": f"{func.__module__}.{func.__qualname__}",
                    "error": str(error),
                    "errorType": type(error).__name__,
                },
            )
            raise

    return wrapper


def logRequest(func: ViewFunction) -> ViewFunction:
    """Log HTTP request details when debug mode is enabled."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not settings.debug:
            return func(*args, **kwargs)

        startTime = time.perf_counter()
        currentUser = getattr(g, "currentUser", None)
        logger.info(
            f"HTTP {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remoteAddr": request.remote_addr,
                "userAgent": request.headers.get("User-Agent"),
                "userId": getattr(currentUser, "id", None),
            },
        )

        try:
            response = func(*args, **kwargs)
        except Exception as error:
            logger.error(
                f"HTTP {request.method} {request.path} -> ERROR",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "error": str(error),
                    "durationMs": round((time.perf_counter() - startTime) * 1000, 2),
                },
                exc_info=True,
            )
            raise

        statusCode = response[1] if isinstance(response, tuple) else 200
        logger.info(
            f"HTTP {request.method} {request.path} -> {statusCode}",
            extra={
                "method": request.method,
                "path": request.path,
                "statusCode": statusCode,
                "durationMs": round((time.perf_counter() - startTime) * 1000, 2),
            },
        )
        return response

    return wrapper
