"""Shared contexts and fixtures for model controller tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
from apps.modules.model.services.gpuExecutionCoordinator import gpuExecutionCoordinator
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
            gpuCoordinator=gpuExecutionCoordinator,
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
            gpuCoordinator=gpuExecutionCoordinator,
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
