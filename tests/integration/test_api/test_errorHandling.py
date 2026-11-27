# tests/integration/test_api/test_errorHandling.py
"""Error envelope: validation, not-found, conflict and traversal protections."""

from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

AUTH = {"Authorization": "Bearer dev-token"}


def errorOf(response: Any) -> dict[str, Any]:
    """Return the `error` object of a JSON error response."""
    payload = response.get_json()
    assert isinstance(payload, dict), payload
    assert "error" in payload, payload
    error: dict[str, Any] = payload["error"]
    return error


def test_body_must_be_json(client: FlaskClient) -> None:
    response = client.post(
        "/api/corpus/pipeline/start",
        headers=AUTH,
        data="sources=wikipedia",
    )

    assert response.status_code == 400
    error = errorOf(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert "Content-Type" in error["message"]


def test_invalid_pipeline_payload_lists_every_field(client: FlaskClient) -> None:
    response = client.post(
        "/api/corpus/pipeline/start",
        headers=AUTH,
        json={"sources": [], "shardSizeTokens": 10, "numWorkers": 0},
    )

    assert response.status_code == 400
    error = errorOf(response)
    assert error["code"] == "VALIDATION_ERROR"
    locations = {entry["loc"][0] for entry in error["details"]}
    assert {"sources", "shardSizeTokens", "numWorkers"} <= locations


def test_unknown_corpus_job_returns_404(client: FlaskClient) -> None:
    response = client.get(
        "/api/corpus/pipeline/missing-job/status",
        headers=AUTH,
    )

    assert response.status_code == 404
    error = errorOf(response)
    assert error["code"] == "RESOURCE_NOT_FOUND"
    assert error["details"] == {"jobId": "missing-job"}


def test_unknown_checkpoint_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/training/checkpoints/nope", headers=AUTH)

    assert response.status_code == 404
    assert errorOf(response)["code"] == "CHECKPOINT_NOT_FOUND"


def test_unknown_tokenizer_job_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/tokenizer/status/nope", headers=AUTH)

    assert response.status_code == 404
    assert errorOf(response)["code"] == "RESOURCE_NOT_FOUND"


def test_non_integer_query_parameter_is_rejected(client: FlaskClient) -> None:
    response = client.get("/api/training/checkpoints?limit=abc", headers=AUTH)

    assert response.status_code == 400
    error = errorOf(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"] == {"value": "abc"}


def test_out_of_range_query_parameter_is_rejected(client: FlaskClient) -> None:
    response = client.get("/api/training/checkpoints?limit=0", headers=AUTH)

    assert response.status_code == 400
    error = errorOf(response)
    assert error["details"]["minimum"] == 1
    assert error["details"]["value"] == 0


def test_tokenizer_path_traversal_is_rejected(client: FlaskClient) -> None:
    response = client.post(
        "/api/tokenizer/encode",
        headers=AUTH,
        json={"tokenizerPath": "../outside.json"},
    )

    assert response.status_code == 400
    error = errorOf(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["path"] == "../outside.json"


def test_invalid_tokenizer_train_payload_is_rejected(client: FlaskClient) -> None:
    response = client.post(
        "/api/tokenizer/train",
        headers=AUTH,
        json={"vocabSize": 10, "numThreads": 0},
    )

    assert response.status_code == 400
    locations = {entry["loc"][0] for entry in errorOf(response)["details"]}
    assert {"vocabSize", "numThreads"} <= locations


def test_empty_preview_text_is_rejected(client: FlaskClient) -> None:
    response = client.post(
        "/api/tokenizer/preview",
        headers=AUTH,
        json={"text": ""},
    )

    assert response.status_code == 400
    assert errorOf(response)["code"] == "VALIDATION_ERROR"


def test_unknown_model_card_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/inference/models/unknown", headers=AUTH)

    assert response.status_code == 404
    assert errorOf(response)["code"] == "CHECKPOINT_NOT_FOUND"
