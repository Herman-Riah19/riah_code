# tests/integration/test_api/test_appWiring.py
"""Application wiring: factory, health, routes, auth gate and CORS."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

EXPECTED_ROUTES = {
    "/health",
    "/api/corpus/pipeline/start",
    "/api/corpus/pipeline/<jobId>/status",
    "/api/corpus/pipeline/<jobId>/resume",
    "/api/corpus/stats",
    "/api/corpus/datasets",
    "/api/corpus/sources",
    "/api/tokenizer/train",
    "/api/tokenizer/encode",
    "/api/tokenizer/status/<jobId>",
    "/api/tokenizer/info",
    "/api/tokenizer/preview",
    "/api/tokenizer/vocab",
    "/api/training/jobs",
    "/api/training/jobs/<jobId>",
    "/api/training/jobs/<jobId>/cancel",
    "/api/training/jobs/<jobId>/resume",
    "/api/training/checkpoints",
    "/api/training/checkpoints/<checkpointId>",
    "/api/training/presets",
    "/api/inference/generate",
    "/api/inference/models",
    "/api/inference/models/<checkpointId>",
}

PROTECTED_ENDPOINTS = (
    ("get", "/api/corpus/stats"),
    ("get", "/api/corpus/datasets"),
    ("get", "/api/corpus/sources"),
    ("post", "/api/corpus/pipeline/start"),
    ("post", "/api/tokenizer/train"),
    ("post", "/api/tokenizer/encode"),
    ("get", "/api/tokenizer/info"),
    ("post", "/api/tokenizer/preview"),
    ("get", "/api/tokenizer/vocab"),
    ("post", "/api/training/jobs"),
    ("get", "/api/training/jobs"),
    ("get", "/api/training/checkpoints"),
    ("get", "/api/training/presets"),
    ("post", "/api/inference/generate"),
    ("get", "/api/inference/models"),
)


def test_health_reports_the_injected_configuration(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "version": "0.0.0-test",
        "env": "testing",
    }


def test_every_module_blueprint_is_registered(app: Flask) -> None:
    registered = {str(rule) for rule in app.url_map.iter_rules()}

    missing = EXPECTED_ROUTES - registered
    assert missing == set()


@pytest.mark.parametrize(("method", "path"), PROTECTED_ENDPOINTS)
def test_protected_endpoints_reject_anonymous_calls(
    client: FlaskClient,
    method: str,
    path: str,
) -> None:
    response = getattr(client, method)(path)

    assert response.status_code == 401
    error = response.get_json()["error"]
    assert error["code"] == "UNAUTHORIZED"
    assert error["details"] == {}


def test_invalid_bearer_token_is_rejected(client: FlaskClient) -> None:
    response = client.get(
        "/api/corpus/stats",
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_cors_headers_are_emitted_for_allowed_origins(client: FlaskClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert "POST" in response.headers["Access-Control-Allow-Methods"]


def test_cors_headers_are_absent_for_unknown_origins(client: FlaskClient) -> None:
    response = client.get("/health", headers={"Origin": "http://evil.test"})

    assert "Access-Control-Allow-Origin" not in response.headers
