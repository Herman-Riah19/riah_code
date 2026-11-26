# tests/unit/test_shared/test_decorators.py
"""Tests for the shared decorators - auth, validation, rate limit, retry, logging."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from flask import Flask, jsonify
from pydantic import BaseModel, Field

from apps.modules.shared.decorators.auth import (
    AuthenticatedUser,
    optionalAuth,
    requireAuth,
    requireRole,
)
from apps.modules.shared.decorators.logging import logErrors, logExecution, logRequest
from apps.modules.shared.decorators.rateLimit import rateLimited
from apps.modules.shared.decorators.retry import circuitBreaker, retryable
from apps.modules.shared.decorators.validation import (
    validateInput,
    validateParams,
    validateQuery,
)
from apps.modules.shared.kernel.exceptions import (
    ForbiddenError,
    RiahAppError,
    UnauthorizedError,
)

AUTH_HEADERS = {"Authorization": "Bearer dev-token"}
INVALID_HEADERS = {"Authorization": "Bearer wrong-token"}


class PayloadSchema(BaseModel):
    """Minimal body schema used by the validation tests."""

    name: str = Field(min_length=1)
    count: int = Field(ge=1)


class QuerySchema(BaseModel):
    """Minimal query schema used by the validation tests."""

    limit: int = Field(ge=1, le=10)


class ParamsSchema(BaseModel):
    """Minimal path-parameter schema used by the validation tests."""

    itemId: int = Field(ge=1)


def buildApp() -> Flask:
    """Create a Flask app exposing every decorator and the error handler."""
    application = Flask(__name__)
    application.config.update(TESTING=True)

    @application.errorhandler(RiahAppError)
    def handleAppError(error: RiahAppError) -> Any:
        response = jsonify(error.to_dict())
        response.status_code = error.statusCode
        return response

    @application.route("/secure")
    @requireAuth
    def secure(user: AuthenticatedUser) -> Any:
        return jsonify({"id": user.id, "role": user.role})

    @application.route("/optional")
    @optionalAuth
    def optional(user: AuthenticatedUser | None) -> Any:
        return jsonify({"id": user.id if user else None})

    @application.route("/admin")
    @requireAuth
    @requireRole("admin")
    def admin(user: AuthenticatedUser) -> Any:
        return jsonify({"id": user.id})

    @application.route("/members")
    @requireAuth
    @requireRole("member")
    def members(user: AuthenticatedUser) -> Any:
        return jsonify({"id": user.id})

    @application.route("/body", methods=["POST"])
    @requireAuth
    @validateInput(PayloadSchema)
    def body(validated: PayloadSchema, user: AuthenticatedUser) -> Any:
        return jsonify({"name": validated.name, "count": validated.count})

    @application.route("/query")
    @requireAuth
    @validateQuery(QuerySchema)
    def query(validated: QuerySchema, user: AuthenticatedUser) -> Any:
        return jsonify({"limit": validated.limit})

    @application.route("/params/<int:itemId>")
    @requireAuth
    @validateParams(ParamsSchema)
    def params(validated: ParamsSchema, user: AuthenticatedUser) -> Any:
        return jsonify({"itemId": validated.itemId})

    @application.route("/limited")
    @rateLimited(maxRequests=2, windowSeconds=60, keyFunc=lambda: "rate-limit-test-key")
    def limited() -> Any:
        return jsonify({"ok": True})

    @application.route("/logged")
    @logExecution(logResult=True)
    @logErrors
    @logRequest
    def logged() -> Any:
        return jsonify({"ok": True})

    @application.route("/logged-error")
    @logErrors
    def loggedError() -> Any:
        raise ValueError("boom")

    return application


@pytest.fixture
def client():
    """Flask test client for the decorator application."""
    return buildApp().test_client()


class TestAuthDecorators:
    """Bearer-token authentication and role checks."""

    def test_require_auth_accepts_the_dev_token(self, client) -> None:
        response = client.get("/secure", headers=AUTH_HEADERS)

        assert response.status_code == 200
        assert response.get_json() == {"id": "dev-user", "role": "admin"}

    def test_require_auth_rejects_a_missing_token(self, client) -> None:
        response = client.get("/secure")

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_require_auth_rejects_an_invalid_token(self, client) -> None:
        response = client.get("/secure", headers=INVALID_HEADERS)

        assert response.status_code == 401

    def test_require_auth_rejects_a_malformed_header(self, client) -> None:
        response = client.get("/secure", headers={"Authorization": "dev-token"})

        assert response.status_code == 401

    def test_optional_auth_without_token(self, client) -> None:
        response = client.get("/optional")

        assert response.status_code == 200
        assert response.get_json()["id"] is None

    def test_optional_auth_with_token(self, client) -> None:
        response = client.get("/optional", headers=AUTH_HEADERS)

        assert response.get_json()["id"] == "dev-user"

    def test_require_role_accepts_allowed_role(self, client) -> None:
        response = client.get("/admin", headers=AUTH_HEADERS)

        assert response.status_code == 200

    def test_require_role_rejects_other_role(self, client) -> None:
        response = client.get("/members", headers=AUTH_HEADERS)

        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "FORBIDDEN"

    def test_require_role_raises_when_user_is_missing(self) -> None:
        view = requireRole("admin")(lambda user: user)

        with pytest.raises(UnauthorizedError):
            view(None)

    def test_validate_token_returns_none_outside_debug(self, monkeypatch) -> None:
        from apps.modules.shared.decorators import auth

        monkeypatch.setattr(auth.settings, "debug", False)
        assert auth._validateToken("dev-token") is None

    def test_require_auth_propagates_forbidden_error(self) -> None:
        with pytest.raises(ForbiddenError):
            requireRole("admin")(lambda user: user)(AuthenticatedUser("u", "user", "e"))


class TestValidationDecorators:
    """Pydantic body, query and path validation."""

    def test_valid_body_is_forwarded(self, client) -> None:
        response = client.post(
            "/body",
            headers=AUTH_HEADERS,
            json={"name": "abc", "count": 3},
        )

        assert response.status_code == 200
        assert response.get_json() == {"name": "abc", "count": 3}

    def test_body_requires_json(self, client) -> None:
        response = client.post("/body", headers=AUTH_HEADERS, data="name=abc")

        assert response.status_code == 400
        assert "Content-Type" in response.get_json()["error"]["message"]

    def test_invalid_body_returns_details(self, client) -> None:
        response = client.post(
            "/body",
            headers=AUTH_HEADERS,
            json={"name": "", "count": 0},
        )

        assert response.status_code == 400
        error = response.get_json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert isinstance(error["details"], list)
        assert {entry["loc"][0] for entry in error["details"]} == {"name", "count"}

    def test_valid_query_is_forwarded(self, client) -> None:
        response = client.get("/query?limit=5", headers=AUTH_HEADERS)

        assert response.status_code == 200
        assert response.get_json() == {"limit": 5}

    def test_invalid_query_is_rejected(self, client) -> None:
        response = client.get("/query?limit=0", headers=AUTH_HEADERS)

        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_valid_params_are_forwarded(self, client) -> None:
        response = client.get("/params/7", headers=AUTH_HEADERS)

        assert response.status_code == 200
        assert response.get_json() == {"itemId": 7}

    def test_invalid_params_are_rejected(self, client) -> None:
        response = client.get("/params/0", headers=AUTH_HEADERS)

        assert response.status_code == 400


class TestRateLimitDecorator:
    """Sliding-window rate limiting."""

    @pytest.fixture(autouse=True)
    def freshLimiter(self, monkeypatch) -> None:
        """Give every test an isolated limiter instance."""
        from apps.modules.shared.decorators import rateLimit

        monkeypatch.setattr(rateLimit, "_rateLimiter", rateLimit.RateLimiter())

    def test_allowed_response_carries_rate_limit_headers(self, client) -> None:
        response = client.get("/limited")

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "2"
        assert response.headers["X-RateLimit-Remaining"] == "1"

    def test_second_and_third_requests(self, client) -> None:
        assert client.get("/limited").status_code == 200
        assert client.get("/limited").status_code == 200

        blocked = client.get("/limited")

        assert blocked.status_code == 429
        assert blocked.get_json()["error"]["code"] == "RATE_LIMITED"

    def test_blocked_request_details(self, client) -> None:
        client.get("/limited")
        client.get("/limited")

        details = client.get("/limited").get_json()["error"]["details"]

        assert details["allowed"] is False
        assert details["limit"] == 2
        assert details["retryAfter"] >= 1

    def test_blocked_request_does_not_call_the_view(self) -> None:
        calls: list[int] = []
        app = Flask(__name__)

        @app.errorhandler(RiahAppError)
        def handleAppError(error: RiahAppError) -> Any:
            response = jsonify(error.to_dict())
            response.status_code = error.statusCode
            return response

        @app.route("/only")
        @rateLimited(maxRequests=1, windowSeconds=60, keyFunc=lambda: "unique-key")
        def only() -> Any:
            calls.append(1)
            return jsonify({"ok": True})

        testClient = app.test_client()
        testClient.get("/only")
        assert testClient.get("/only").status_code == 429
        assert len(calls) == 1


class TestRetryAndCircuitBreaker:
    """Retry backoff and circuit breaker transitions."""

    def test_retryable_eventually_succeeds(self, monkeypatch) -> None:
        monkeypatch.setattr("time.sleep", lambda seconds: None)
        attempts: list[int] = []

        @retryable(maxAttempts=3, baseDelay=0.0, jitter=False)
        def flaky() -> str:
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("not yet")
            return "ok"

        assert flaky() == "ok"
        assert len(attempts) == 3

    def test_retryable_reraises_after_exhaustion(self, monkeypatch) -> None:
        monkeypatch.setattr("time.sleep", lambda seconds: None)

        @retryable(maxAttempts=2, baseDelay=0.0, jitter=False)
        def alwaysFails() -> None:
            raise ValueError("nope")

        with pytest.raises(ValueError, match="nope"):
            alwaysFails()

    def test_retryable_ignores_non_matching_exceptions(self, monkeypatch) -> None:
        monkeypatch.setattr("time.sleep", lambda seconds: None)

        @retryable(maxAttempts=3, retryableExceptions=(KeyError,), jitter=False)
        def wrongError() -> None:
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            wrongError()

    def test_circuit_breaker_opens_then_rejects(self) -> None:
        breakerCalls: list[int] = []

        @circuitBreaker(failureThreshold=2, recoveryTimeout=60.0)
        def failing() -> None:
            breakerCalls.append(1)
            raise ValueError("down")

        with pytest.raises(ValueError):
            failing()
        with pytest.raises(ValueError):
            failing()

        with pytest.raises(RiahAppError, match="Circuit breaker"):
            failing()
        assert len(breakerCalls) == 2

    def test_circuit_breaker_stays_open_until_recovery_timeout(self) -> None:
        shouldFail = {"value": True}

        @circuitBreaker(failureThreshold=1, recoveryTimeout=60.0)
        def toggle() -> str:
            if shouldFail["value"]:
                raise ValueError("down")
            return "ok"

        with pytest.raises(ValueError):
            toggle()
        shouldFail["value"] = False
        with pytest.raises(RiahAppError):
            toggle()

    def test_circuit_breaker_closes_after_recovery(self) -> None:
        shouldFail = {"value": True}

        @circuitBreaker(failureThreshold=1, recoveryTimeout=-1.0)
        def toggle() -> str:
            if shouldFail["value"]:
                raise ValueError("down")
            return "ok"

        with pytest.raises(ValueError):
            toggle()
        shouldFail["value"] = False

        assert toggle() == "ok"


class TestLoggingDecorators:
    """Logging decorators keep behaviour unchanged."""

    def test_logged_view_returns_the_response(self, client) -> None:
        response = client.get("/logged")

        assert response.status_code == 200
        assert response.get_json() == {"ok": True}

    def test_logged_error_still_propagates(self, client) -> None:
        with pytest.raises(ValueError, match="boom"):
            client.get("/logged-error")

    def test_log_execution_logs_when_called(self, caplog) -> None:
        @logExecution(logArgs=True, logResult=True, logLevel=logging.INFO)
        def add(left: int, right: int) -> int:
            return left + right

        with caplog.at_level(logging.INFO):
            assert add(2, 3) == 5

        assert "Executing" in caplog.text
        assert "Completed" in caplog.text
