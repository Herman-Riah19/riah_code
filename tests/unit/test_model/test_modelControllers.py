# tests/unit/test_model/test_modelControllers.py
"""Tests for the training and inference HTTP controllers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fakes import (
    DeferredWorkerPool,
    FakeTokenizerRepository,
    InlineWorkerPool,
    cpuModelFactory,
    makeCheckpoint,
)
from flask import Flask, jsonify
from tinyShards import writeTinyShard

from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.model.controllers.inferenceController import (
    InferenceContainer,
    inferenceBlueprint,
)
from apps.modules.model.controllers.trainingController import (
    TrainingContainer,
    trainingBlueprint,
)
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.model.services.inferenceService import InferenceService
from apps.modules.model.services.trainingService import TrainingService
from apps.modules.shared.kernel.exceptions import RiahAppError
from apps.modules.shared.kernel.job import JobRepository
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository

AUTH_HEADERS = {"Authorization": "Bearer dev-token"}

TRAIN_PAYLOAD: dict[str, Any] = {
    "preset": "tiny",
    "modelName": "tiny-test",
    "batchSize": 2,
    "seqLen": 8,
    "maxSteps": 1,
    "evalInterval": 1,
    "checkpointInterval": 1,
    "logInterval": 0,
    "numWorkers": 0,
    "compileModel": False,
    "dtype": "fp32",
}


def buildApp(*blueprints) -> Flask:
    """Create a test Flask app exposing the domain error handler."""
    application = Flask(__name__)
    application.config.update(TESTING=True)

    @application.errorhandler(RiahAppError)
    def handleAppError(error: RiahAppError):
        response = jsonify(error.to_dict())
        response.status_code = error.statusCode
        return response

    for blueprint in blueprints:
        application.register_blueprint(blueprint)
    return application


def errorCode(response) -> str:
    """Return the domain error code of a failed response."""
    return str(response.get_json()["error"]["code"])


class TrainingContext:
    """Bundle the training container overrides and the test client."""

    def __init__(self, tmp_path: Path, monkeypatch, *, inline: bool = True) -> None:
        self.checkpointRepo = CheckpointRepository(tmp_path / "checkpoints")
        self.tokenizerRepo = TokenizerRepository(tmp_path / "tokenizer")
        self.corpusRepo = CorpusRepository(tmp_path / "corpus")
        self.jobRepo = JobRepository()
        self.pool = InlineWorkerPool() if inline else DeferredWorkerPool()
        self.service = TrainingService(
            modelFactory=cpuModelFactory,
            tokenizerRepo=self.tokenizerRepo,
            checkpointRepo=self.checkpointRepo,
            corpusRepo=self.corpusRepo,
            jobRepo=self.jobRepo,
            workerPool=self.pool,
            defaultCheckpointDir=tmp_path / "runs",
        )
        monkeypatch.setattr(TrainingContainer, "_checkpointRepository", self.checkpointRepo)
        monkeypatch.setattr(TrainingContainer, "_tokenizerRepository", self.tokenizerRepo)
        monkeypatch.setattr(TrainingContainer, "_corpusRepository", self.corpusRepo)
        monkeypatch.setattr(TrainingContainer, "_jobRepository", self.jobRepo)
        monkeypatch.setattr(TrainingContainer, "_workerPool", self.pool)
        monkeypatch.setattr(TrainingContainer, "_service", self.service)

        self.app = buildApp(trainingBlueprint)
        self.client = self.app.test_client()
        self.shard = writeTinyShard(
            self.corpusRepo.getShardDir(),
            name="shard_000001.bin",
            seed=17,
        )

    def start(self, **overrides: Any):
        """Post a training job with the default payload plus overrides."""
        return self.client.post(
            "/api/training/jobs",
            headers=AUTH_HEADERS,
            json={**TRAIN_PAYLOAD, **overrides},
        )


class InferenceContext:
    """Bundle the inference container overrides and the test client."""

    def __init__(self, tmp_path: Path, monkeypatch) -> None:
        self.checkpointRepo = CheckpointRepository(tmp_path / "checkpoints")
        self.tokenizerRepo = FakeTokenizerRepository()
        self.service = InferenceService(
            tokenizerRepo=self.tokenizerRepo,  # type: ignore[arg-type]
            checkpointRepo=self.checkpointRepo,
            modelFactory=cpuModelFactory,
            cacheCapacity=2,
        )
        monkeypatch.setattr(InferenceContainer, "_checkpointRepository", self.checkpointRepo)
        monkeypatch.setattr(InferenceContainer, "_tokenizerRepository", self.tokenizerRepo)
        monkeypatch.setattr(InferenceContainer, "_service", self.service)

        self.app = buildApp(inferenceBlueprint)
        self.client = self.app.test_client()
        self.checkpoint = makeCheckpoint(
            tmp_path,
            self.checkpointRepo,
            "ckpt-a",
            isBest=True,
            modelName="tiny-test",
        )


@pytest.fixture
def training(tmp_path: Path, monkeypatch) -> TrainingContext:
    """Training controller wired to temporary repositories."""
    return TrainingContext(tmp_path, monkeypatch)


@pytest.fixture
def deferredTraining(tmp_path: Path, monkeypatch) -> TrainingContext:
    """Training controller whose worker pool never runs the job."""
    return TrainingContext(tmp_path, monkeypatch, inline=False)


@pytest.fixture
def inference(tmp_path: Path, monkeypatch) -> InferenceContext:
    """Inference controller wired to a fake tokenizer and one checkpoint."""
    return InferenceContext(tmp_path, monkeypatch)


class TestTrainingControllerWiring:
    """Blueprint metadata and authentication."""

    def test_blueprint_metadata(self) -> None:
        assert trainingBlueprint.name == "training"
        assert trainingBlueprint.url_prefix == "/api/training"

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("get", "/api/training/jobs"),
            ("get", "/api/training/jobs/unknown"),
            ("get", "/api/training/checkpoints"),
            ("get", "/api/training/checkpoints/unknown"),
            ("get", "/api/training/presets"),
            ("post", "/api/training/jobs"),
            ("post", "/api/training/jobs/unknown/cancel"),
            ("post", "/api/training/jobs/unknown/resume"),
        ],
    )
    def test_endpoints_require_auth(
        self, training: TrainingContext, method: str, path: str
    ) -> None:
        response = getattr(training.client, method)(path)

        assert response.status_code == 401
        assert errorCode(response) == "UNAUTHORIZED"

    def test_presets_lists_architectures(self, training: TrainingContext) -> None:
        response = training.client.get("/api/training/presets", headers=AUTH_HEADERS)

        assert response.status_code == 200
        payload = response.get_json()
        names = [entry["name"] for entry in payload]
        assert "tiny" in names
        tinyPreset = next(entry for entry in payload if entry["name"] == "tiny")
        assert tinyPreset["modelConfig"]["dim"] == 64
        assert tinyPreset["parameters"] > 0


class TestTrainingControllerStart:
    """Launching training jobs over HTTP."""

    def test_start_returns_202_and_completed_job(self, training: TrainingContext) -> None:
        response = training.start()

        assert response.status_code == 202
        payload = response.get_json()
        assert payload["jobType"] == "training"
        assert payload["status"] == "completed"
        assert payload["result"]["steps"] == 1
        assert payload["progress"]["step"] == 1
        assert payload["userId"] == "dev-user"

    def test_start_rejects_unknown_preset(self, training: TrainingContext) -> None:
        response = training.start(preset="galactic")

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_rejects_seq_len_above_context(self, training: TrainingContext) -> None:
        response = training.start(seqLen=4096)

        assert response.status_code == 400
        error = response.get_json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert "seqLen" in error["message"]

    def test_start_rejects_invalid_hyper_parameter(self, training: TrainingContext) -> None:
        response = training.start(batchSize=0)

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_requires_json_content_type(self, training: TrainingContext) -> None:
        response = training.client.post(
            "/api/training/jobs",
            headers=AUTH_HEADERS,
            data="preset=tiny",
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_without_any_shard_fails_before_queueing(self, training: TrainingContext) -> None:
        training.shard.unlink()
        training.shard.with_suffix(".idx").unlink()

        response = training.start()

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_with_explicit_shard(self, training: TrainingContext) -> None:
        response = training.start(trainShards=[str(training.shard)])

        assert response.status_code == 202
        assert response.get_json()["status"] == "completed"

    def test_start_rejects_shard_outside_the_corpus(
        self, training: TrainingContext, tmp_path: Path
    ) -> None:
        outsideShard = writeTinyShard(tmp_path / "outside", name="other.bin")

        response = training.start(trainShards=[str(outsideShard)])

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"
        assert training.checkpointRepo.count() == 0

    def test_start_queues_a_job_without_running_it(self, deferredTraining: TrainingContext) -> None:
        response = deferredTraining.start()

        assert response.status_code == 202
        payload = response.get_json()
        assert payload["status"] == "pending"
        assert payload["result"] is None
        assert len(deferredTraining.pool.tasks) == 1


class TestTrainingControllerJobs:
    """Job listing, inspection and cancellation."""

    def test_list_jobs_returns_created_job(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.get("/api/training/jobs", headers=AUTH_HEADERS)

        assert response.status_code == 200
        assert [job["id"] for job in response.get_json()] == [created["id"]]

    @pytest.mark.parametrize("query", ["limit=zero", "limit=0", "limit=201"])
    def test_list_jobs_rejects_invalid_limit(self, training: TrainingContext, query: str) -> None:
        response = training.client.get(
            f"/api/training/jobs?{query}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_get_job(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.get(
            f"/api/training/jobs/{created['id']}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.get_json()["id"] == created["id"]

    def test_get_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.get(
            "/api/training/jobs/unknown",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert errorCode(response) == "RESOURCE_NOT_FOUND"

    def test_cancel_pending_job(self, deferredTraining: TrainingContext) -> None:
        created = deferredTraining.start().get_json()

        response = deferredTraining.client.post(
            f"/api/training/jobs/{created['id']}/cancel",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "cancelled"
        assert payload["progress"]["cancelRequested"] is True

    def test_cancel_completed_job_returns_409(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/cancel",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 409
        assert errorCode(response) == "INVALID_JOB_STATE"

    def test_cancel_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.post(
            "/api/training/jobs/unknown/cancel",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404


class TestTrainingControllerResume:
    """Resuming a job from its latest checkpoint."""

    def test_resume_creates_a_new_completed_job(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={"maxSteps": 2},
        )

        assert response.status_code == 202
        payload = response.get_json()
        assert payload["id"] != created["id"]
        assert payload["status"] == "completed"
        assert payload["resumeFrom"] is not None
        assert payload["result"]["steps"] == 2

    def test_resume_without_overrides(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={},
        )

        assert response.status_code == 202
        assert response.get_json()["status"] == "completed"

    def test_resume_rejects_invalid_overrides(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={"maxSteps": 0},
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_resume_with_unknown_checkpoint_returns_404(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={"checkpointId": "missing"},
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"

    def test_resume_pending_job_without_checkpoint_returns_404(
        self, deferredTraining: TrainingContext
    ) -> None:
        created = deferredTraining.start().get_json()

        response = deferredTraining.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={},
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"

    def test_resume_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.post(
            "/api/training/jobs/unknown/resume",
            headers=AUTH_HEADERS,
            json={},
        )

        assert response.status_code == 404


class TestTrainingControllerCheckpoints:
    """Checkpoint listing and lookup."""

    def test_list_checkpoints(self, training: TrainingContext) -> None:
        training.start()

        response = training.client.get(
            "/api/training/checkpoints",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload
        assert all(entry["path"] for entry in payload)

    def test_list_checkpoints_filters_by_model_name(self, training: TrainingContext) -> None:
        training.start()

        found = training.client.get(
            "/api/training/checkpoints?modelName=tiny-test",
            headers=AUTH_HEADERS,
        )
        missing = training.client.get(
            "/api/training/checkpoints?modelName=other",
            headers=AUTH_HEADERS,
        )

        assert found.get_json()
        assert missing.get_json() == []

    @pytest.mark.parametrize("query", ["limit=0", "offset=-1", "offset=zero"])
    def test_list_checkpoints_rejects_invalid_bounds(
        self, training: TrainingContext, query: str
    ) -> None:
        response = training.client.get(
            f"/api/training/checkpoints?{query}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400

    def test_get_checkpoint(self, training: TrainingContext) -> None:
        training.start()
        latest = training.checkpointRepo.findLatest()
        assert latest is not None

        response = training.client.get(
            f"/api/training/checkpoints/{latest.id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.get_json()["id"] == latest.id

    def test_get_unknown_checkpoint_returns_404(self, training: TrainingContext) -> None:
        response = training.client.get(
            "/api/training/checkpoints/missing",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"


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
