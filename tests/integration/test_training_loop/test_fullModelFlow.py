# tests/integration/test_training_loop/test_fullModelFlow.py
"""One request chain across every module: corpus, tokenizer, training, inference."""

from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

AUTH = {"Authorization": "Bearer dev-token"}


def test_corpus_to_inference_end_to_end(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    trainingResponse = client.post(
        "/api/training/jobs",
        headers=AUTH,
        json={
            "preset": "tiny",
            "modelName": "flow-tiny",
            "seqLen": 16,
            "batchSize": 2,
            "maxSteps": 1,
            "evalInterval": 0,
            "evalSteps": 1,
            "checkpointInterval": 0,
            "logInterval": 0,
            "dtype": "fp32",
            "compileModel": False,
            "scheduler": "constant",
            "warmupSteps": 0,
            "saveRng": False,
            "numWorkers": 0,
        },
    )

    assert trainingResponse.status_code == 202, trainingResponse.get_json()
    trainingJob = trainingResponse.get_json()
    assert encodedShards["status"] == "completed"
    assert trainingJob["status"] == "completed", trainingJob

    checkpointId = f"{trainingJob['id']}:final"
    modelsResponse = client.get("/api/inference/models", headers=AUTH)
    assert checkpointId in {model["id"] for model in modelsResponse.get_json()}

    generationResponse = client.post(
        "/api/inference/generate",
        headers=AUTH,
        json={
            "prompt": "Le corpus de test",
            "checkpointId": checkpointId,
            "maxTokens": 2,
            "temperature": 0.0,
            "topK": 1,
            "topP": 1.0,
            "repetitionPenalty": 1.0,
        },
    )

    assert generationResponse.status_code == 200, generationResponse.get_json()
    output = generationResponse.get_json()
    assert output["checkpointId"] == checkpointId
    assert 0 <= output["generatedTokens"] <= 2
    assert output["prompt"] == "Le corpus de test"
