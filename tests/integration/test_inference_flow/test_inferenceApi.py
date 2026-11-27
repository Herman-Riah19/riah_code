# tests/integration/test_inference_flow/test_inferenceApi.py
"""Inference module through the HTTP API: generation and model cards."""

from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient

from apps.modules.model.models.modelModel import Checkpoint

pytestmark = pytest.mark.integration

AUTH = {"Authorization": "Bearer dev-token"}


def generationPayload(checkpointId: str | None, **overrides: Any) -> dict[str, Any]:
    """Greedy generation request with an exact token budget."""
    payload: dict[str, Any] = {
        "prompt": "Le corpus de test",
        "maxTokens": 3,
        "temperature": 0.0,
        "topK": 1,
        "topP": 1.0,
        "repetitionPenalty": 1.0,
    }
    if checkpointId is not None:
        payload["checkpointId"] = checkpointId
    payload.update(overrides)
    return payload


def test_generate_returns_the_requested_number_of_tokens(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload(seededCheckpoint.id),
    )

    assert response.status_code == 200, response.get_json()
    output = response.get_json()
    assert output["prompt"] == "Le corpus de test"
    assert output["checkpointId"] == seededCheckpoint.id
    assert output["generatedTokens"] == 3
    assert isinstance(output["completion"], str)
    assert isinstance(output["text"], str)


def test_generate_without_checkpoint_uses_the_best_model(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload(None),
    )

    assert response.status_code == 200
    assert response.get_json()["checkpointId"] == seededCheckpoint.id


def test_stop_sequences_are_resolved_through_the_tokenizer(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload(seededCheckpoint.id, stopSequences=["test"], maxTokens=5),
    )

    assert response.status_code == 200
    output = response.get_json()
    assert 0 <= output["generatedTokens"] <= 5


def test_generate_rejects_an_unknown_checkpoint(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload("missing-checkpoint"),
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "CHECKPOINT_NOT_FOUND"


def test_generate_requires_a_tokenizer(client: FlaskClient, seededCheckpoint: Checkpoint) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload(seededCheckpoint.id),
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "TOKENIZER_NOT_FOUND"


def test_generate_requires_a_checkpoint(
    client: FlaskClient, trainedTokenizer: dict[str, Any]
) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload(None),
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NO_MODEL_AVAILABLE"


def test_generate_rejects_a_blank_prompt(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    response = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json=generationPayload(seededCheckpoint.id, prompt="   "),
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_models_lists_the_available_checkpoints(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    response = client.get("/api/inference/models", headers=AUTH)

    assert response.status_code == 200
    models = response.get_json()
    assert [model["id"] for model in models] == [seededCheckpoint.id]
    model = models[0]
    assert model["modelName"] == "seed"
    assert model["isBest"] is True
    assert model["parameters"] > 0
    assert model["architecture"]["vocabSize"] == 512


def test_model_card_matches_the_listing(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
    seededCheckpoint: Checkpoint,
) -> None:
    listResponse = client.get("/api/inference/models", headers=AUTH)
    cardResponse = client.get(
        f"/api/inference/models/{seededCheckpoint.id}",
        headers=AUTH,
    )

    assert cardResponse.status_code == 200
    assert cardResponse.get_json() == listResponse.get_json()[0]


def test_models_listing_is_empty_without_checkpoints(client: FlaskClient) -> None:
    response = client.get("/api/inference/models", headers=AUTH)

    assert response.status_code == 200
    assert response.get_json() == []


def test_models_listing_validates_the_limit(client: FlaskClient) -> None:
    response = client.get("/api/inference/models?limit=0", headers=AUTH)

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"
