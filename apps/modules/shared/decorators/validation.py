# apps/modules/shared/decorators/validation.py
"""Request validation decorators."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import request
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from apps.modules.shared.kernel.exceptions import ValidationError

ViewFunction = TypeVar("ViewFunction", bound=Callable[..., Any])
ValidatedFunction = Callable[..., Any]


def _validationDetails(error: PydanticValidationError) -> list[Any]:
    """Serialize a Pydantic error without leaking URLs, contexts or inputs."""
    return cast(
        "list[Any]",
        error.errors(
            include_url=False,
            include_context=False,
            include_input=False,
        ),
    )


def validateInput(schema: type[BaseModel]) -> Callable[[ViewFunction], ValidatedFunction]:
    """Decorator to validate JSON request body against a Pydantic schema."""

    def decorator(func: ViewFunction) -> ValidatedFunction:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not request.is_json:
                raise ValidationError("Content-Type doit être application/json")

            try:
                validated = schema(**request.get_json())
            except PydanticValidationError as error:
                raise ValidationError(
                    "Données invalides",
                    details=_validationDetails(error),
                ) from None

            return func(validated, *args, **kwargs)

        return wrapper

    return decorator


def validateQuery(schema: type[BaseModel]) -> Callable[[ViewFunction], ValidatedFunction]:
    """Decorator to validate query parameters."""

    def decorator(func: ViewFunction) -> ValidatedFunction:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                validated = schema(**request.args.to_dict())
            except PydanticValidationError as error:
                raise ValidationError(
                    "Paramètres de requête invalides",
                    details=_validationDetails(error),
                ) from None
            return func(validated, *args, **kwargs)

        return wrapper

    return decorator


def validateParams(schema: type[BaseModel]) -> Callable[[ViewFunction], ValidatedFunction]:
    """Decorator to validate URL path parameters."""

    def decorator(func: ViewFunction) -> ValidatedFunction:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                validated = schema(**kwargs)
            except PydanticValidationError as error:
                raise ValidationError(
                    "Paramètres d'URL invalides",
                    details=_validationDetails(error),
                ) from None
            return func(validated, *args, **kwargs)

        return wrapper

    return decorator
