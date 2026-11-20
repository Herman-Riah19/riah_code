# apps/modules/shared/decorators/auth.py
"""Authentication decorators"""
from functools import wraps
from flask import request, g
from apps.modules.shared.kernel.exceptions import UnauthorizedError, ForbiddenError
from apps.modules.shared.config import settings


def requireAuth(func):
    """Decorator to require valid authentication token"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        authHeader = request.headers.get("Authorization")
        if not authHeader or not authHeader.startswith("Bearer "):
            raise UnauthorizedError("Token manquant ou invalide")
        
        token = authHeader[7:]  # Remove "Bearer "
        user = _validateToken(token)
        if not user:
            raise UnauthorizedError("Token invalide ou expiré")
        
        g.currentUser = user
        return func(user, *args, **kwargs)
    return wrapper


def optionalAuth(func):
    """Decorator for optional authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        authHeader = request.headers.get("Authorization")
        user = None
        if authHeader and authHeader.startswith("Bearer "):
            token = authHeader[7:]
            user = _validateToken(token)
        g.currentUser = user
        return func(user, *args, **kwargs)
    return wrapper


def requireRole(*roles: str):
    """Decorator to require specific role(s)"""
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            if not user:
                raise UnauthorizedError("Authentification requise")
            userRole = getattr(user, "role", "user")
            if userRole not in roles:
                raise ForbiddenError(f"Rôle requis: {', '.join(roles)}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def _validateToken(token: str):
    """Validate JWT token - implement your logic here"""
    # TODO: Implement JWT validation with PyJWT
    # For now, return mock user for development
    if settings.debug and token == "dev-token":
        return type("User", (), {"id": "dev-user", "role": "admin", "email": "dev@local"})()
    return None