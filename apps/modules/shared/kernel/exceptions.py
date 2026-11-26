# apps/modules/shared/kernel/exceptions.py
"""Domain exceptions hierarchy"""

from typing import Any

ErrorDetails = dict[str, Any] | list[Any]


class RiahAppError(Exception):
    """Base exception for all application errors"""

    statusCode: int = 500
    errorCode: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: ErrorDetails | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: ErrorDetails = details if details is not None else {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.errorCode,
                "message": self.message,
                "details": self.details,
            }
        }


class ResourceNotFoundError(RiahAppError):
    statusCode = 404
    errorCode = "RESOURCE_NOT_FOUND"


class ValidationError(RiahAppError):
    statusCode = 400
    errorCode = "VALIDATION_ERROR"


class UnauthorizedError(RiahAppError):
    statusCode = 401
    errorCode = "UNAUTHORIZED"


class ForbiddenError(RiahAppError):
    statusCode = 403
    errorCode = "FORBIDDEN"


class InvalidJobStateError(RiahAppError):
    statusCode = 409
    errorCode = "INVALID_JOB_STATE"


class CheckpointNotFoundError(ResourceNotFoundError):
    errorCode = "CHECKPOINT_NOT_FOUND"


class NoModelAvailableError(ResourceNotFoundError):
    errorCode = "NO_MODEL_AVAILABLE"


class TokenizerNotFoundError(ResourceNotFoundError):
    errorCode = "TOKENIZER_NOT_FOUND"


class CancellationException(RiahAppError):  # noqa: N818 - name kept for the PRD contract
    statusCode = 499
    errorCode = "CANCELLED"


class RateLimitError(RiahAppError):
    statusCode = 429
    errorCode = "RATE_LIMITED"
