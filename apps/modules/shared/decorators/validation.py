# apps/modules/shared/decorators/validation.py
"""Request validation decorators"""
from functools import wraps
from flask import request
from pydantic import BaseModel, ValidationError as PydanticValidationError
from apps.modules.shared.kernel.exceptions import ValidationError


def validateInput(schema: type[BaseModel]):
    """Decorator to validate JSON request body against Pydantic schema"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                raise ValidationError("Content-Type doit être application/json")
            
            try:
                validated = schema(**request.get_json())
            except PydanticValidationError as e:
                raise ValidationError("Données invalides", details=e.errors())
            
            return func(validated, *args, **kwargs)
        return wrapper
    return decorator


def validateQuery(schema: type[BaseModel]):
    """Decorator to validate query parameters"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validated = schema(**request.args.to_dict())
            except PydanticValidationError as e:
                raise ValidationError("Paramètres de requête invalides", details=e.errors())
            return func(validated, *args, **kwargs)
        return wrapper
    return decorator


def validateParams(schema: type[BaseModel]):
    """Decorator to validate URL path parameters"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validated = schema(**kwargs)
            except PydanticValidationError as e:
                raise ValidationError("Paramètres d'URL invalides", details=e.errors())
            return func(validated, *args, **kwargs)
        return wrapper
    return decorator