# apps/modules/shared/decorators/auth.py
"""Authentication decorators."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from flask import g, request

from apps.modules.shared.config import settings
from apps.modules.shared.kernel.exceptions import ForbiddenError, UnauthorizedError

ViewFunction = Callable[..., Any]


@dataclass(frozen=True)
class AuthenticatedUser:
    """Minimal user identity propagated to view functions."""

    id: str
    role: str
    email: str


def requireAuth(func: ViewFunction) -> ViewFunction:
    """Require a valid bearer token and inject the user as first argument."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def optionalAuth(func: ViewFunction) -> ViewFunction:
    """Inject the user when a valid token is present, otherwise None."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        authHeader = request.headers.get("Authorization")
        user = None
        if authHeader and authHeader.startswith("Bearer "):
            token = authHeader[7:]
            user = _validateToken(token)
        g.currentUser = user
        return func(user, *args, **kwargs)

    return wrapper


def requireRole(*roles: str) -> Callable[[ViewFunction], ViewFunction]:
    """Require the injected user to own one of the given roles."""

    def decorator(func: ViewFunction) -> ViewFunction:
        @wraps(func)
        def wrapper(user: AuthenticatedUser | None, *args: Any, **kwargs: Any) -> Any:
            if not user:
                raise UnauthorizedError("Authentification requise")
            userRole = getattr(user, "role", "user")
            if userRole not in roles:
                raise ForbiddenError(f"Rôle requis: {', '.join(roles)}")
            return func(user, *args, **kwargs)

        return wrapper

    return decorator


def _validateToken(token: str) -> AuthenticatedUser | None:
    """Validate a JWT token - mock implementation for development."""
    # TODO: Implement JWT validation with PyJWT
    if settings.debug and token == "dev-token":
        return AuthenticatedUser(id="dev-user", role="admin", email="dev@local")
    return None
