"""Inference HTTP controller contract tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from apps.modules.model.controllers.inferenceController import inferenceBlueprint
from apps.modules.model.services.gpuExecutionCoordinator import gpuExecutionCoordinator
from controllerTestFixtures import AUTH_HEADERS, InferenceContext, errorCode
from fakes import makeCheckpoint


@pytest.fixture
def inference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> InferenceContext:
    """Inference controller wired to a fake tokenizer and one checkpoint."""
    return InferenceContext(tmp_path, monkeypatch)


class TestInferenceControllerWiring:
    """Blueprint metadata and authentication."""

    def test_blueprint_metadata(self) -> None:
        assert inferenceBlueprint.name == "inference"
        assert inferenceBlueprint.url_prefix == "/api/inference"

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("get", "/api/inference/models"),
            ("get", "/api/inference/models/unknown"),
            ("post", "/api/inference/generate"),
        ],
    )
    def test_endpoints_require_auth(
        self, inference: InferenceContext, method: str, path: str
    ) -> None:
        response = getattr(inference.client, method)(path)

        assert response.status_code == 401
        assert errorCode(response) == "UNAUTHORIZED"


class TestInferenceControllerModels:
    """Model cards exposed to the dashboard."""

    def test_list_models(self, inference: InferenceContext) -> None:
        response = inference.client.get(
            "/api/inference/models",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert [card["id"] for card in payload] == ["ckpt-a"]
        card = payload[0]
        assert card["modelName"] == "tiny-test"
        assert card["architecture"]["vocabSize"] == 64

    @pytest.mark.parametrize("query", ["limit=0", "limit=zero"])
    def test_list_models_rejects_invalid_limit(
        self, inference: InferenceContext, query: str
    ) -> None:
        response = inference.client.get(
            f"/api/inference/models?{query}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400

    def test_get_model(self, inference: InferenceContext) -> None:
        response = inference.client.get(
            "/api/inference/models/ckpt-a",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.get_json()["id"] == "ckpt-a"

    def test_get_unknown_model_returns_404(self, inference: InferenceContext) -> None:
        response = inference.client.get(
            "/api/inference/models/missing",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"


class TestInferenceControllerGenerate:
    """Text generation over HTTP."""

    def test_generate_returns_completion(self, inference: InferenceContext) -> None:
        response = inference.client.post(
            "/api/inference/generate",
            headers=AUTH_HEADERS,
            json={
                "prompt": "abc",
                "maxTokens": 2,
                "temperature": 0.0,
                "checkpointId": "ckpt-a",
            },
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["prompt"] == "abc"
        assert payload["completion"] == "aa"
        assert payload["generatedTokens"] == 2
        assert payload["checkpointId"] == "ckpt-a"

    def test_generate_returns_503_when_training_owns_the_gpu(
        self, inference: InferenceContext
    ) -> None:
        with gpuExecutionCoordinator.training():
            response = inference.client.post(
                "/api/inference/generate",
                headers=AUTH_HEADERS,
                json={"prompt": "abc", "maxTokens": 1},
            )

        assert response.status_code == 503
        assert errorCode(response) == "GPU_BUSY"

    def test_generate_uses_the_best_checkpoint_by_default(
        self, inference: InferenceContext
    ) -> None:
        makeCheckpoint(
            inference.checkpoint.path.parent,
            inference.checkpointRepo,
            "ckpt-b",
            step=1,
            modelName="tiny-test",
        )

        response = inference.client.post(
            "/api/inference/generate",
            headers=AUTH_HEADERS,
            json={"prompt": "abc", "maxTokens": 1, "temperature": 0.0},
        )

        assert response.status_code == 200
        assert response.get_json()["checkpointId"] == "ckpt-a"

    def test_generate_accepts_stop_sequences(self, inference: InferenceContext) -> None:
        response = inference.client.post(
            "/api/inference/generate",
            headers=AUTH_HEADERS,
            json={
                "prompt": "abc",
                "maxTokens": 2,
                "temperature": 0.0,
                "stopSequences": ["</s>"],
            },
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "payload",
        [
            {"prompt": ""},
            {"prompt": "abc", "maxTokens": 0},
            {"prompt": "abc", "temperature": 5.1},
            {"prompt": "abc", "topP": 0.0},
            {"prompt": "abc", "repetitionPenalty": 0.0},
            {"prompt": "abc", "stopSequences": [str(index) for index in range(17)]},
        ],
    )
    def test_generate_rejects_invalid_payload(
        self, inference: InferenceContext, payload: dict[str, Any]
    ) -> None:
        response = inference.client.post(
            "/api/inference/generate",
            headers=AUTH_HEADERS,
            json=payload,
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_generate_unknown_checkpoint_returns_404(self, inference: InferenceContext) -> None:
        response = inference.client.post(
            "/api/inference/generate",
            headers=AUTH_HEADERS,
            json={"prompt": "abc", "maxTokens": 1, "checkpointId": "missing"},
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"

    def test_generate_requires_json(self, inference: InferenceContext) -> None:
        response = inference.client.post(
            "/api/inference/generate",
            headers=AUTH_HEADERS,
            data="prompt=abc",
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"
