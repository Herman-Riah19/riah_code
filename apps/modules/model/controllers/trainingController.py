# apps/modules/model/controllers/trainingController.py
"""Training HTTP controller and lazy composition root."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.config import settings
from apps.modules.shared.decorators.auth import requireAuth
from apps.modules.shared.decorators.validation import validateInput
from apps.modules.shared.kernel.exceptions import ValidationError
from apps.modules.shared.kernel.job import JobRepository
from apps.modules.shared.kernel.workerPool import WorkerPool
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository

from ..ml.modelRunner import ModelRunner
from ..models.modelModel import (
    ModelConfig,
    TrainingConfig,
    TrainingResumeRequest,
    TrainingStartRequest,
)
from ..repositories.checkpointRepository import CheckpointRepository
from ..services.trainingService import TrainingService

DEFAULT_WORKER_COUNT = 1

trainingBlueprint = Blueprint("training", __name__, url_prefix="/api/training")


class TrainingContainer:
    """Lazily build and reuse the model-training dependencies."""

    _checkpointRepository: CheckpointRepository | None = None
    _tokenizerRepository: TokenizerRepository | None = None
    _corpusRepository: CorpusRepository | None = None
    _jobRepository: JobRepository | None = None
    _workerPool: WorkerPool | None = None
    _service: TrainingService | None = None

    @classmethod
    def getCheckpointRepository(cls) -> CheckpointRepository:
        if cls._checkpointRepository is None:
            cls._checkpointRepository = CheckpointRepository(settings.checkpointDir)
        return cls._checkpointRepository

    @classmethod
    def getTokenizerRepository(cls) -> TokenizerRepository:
        if cls._tokenizerRepository is None:
            cls._tokenizerRepository = TokenizerRepository(settings.tokenizerDir)
        return cls._tokenizerRepository

    @classmethod
    def getCorpusRepository(cls) -> CorpusRepository:
        if cls._corpusRepository is None:
            cls._corpusRepository = CorpusRepository(settings.corpusDir)
        return cls._corpusRepository

    @classmethod
    def getJobRepository(cls) -> JobRepository:
        if cls._jobRepository is None:
            cls._jobRepository = JobRepository()
        return cls._jobRepository

    @classmethod
    def getWorkerPool(cls) -> WorkerPool:
        if cls._workerPool is None:
            cls._workerPool = WorkerPool(maxWorkers=DEFAULT_WORKER_COUNT)
        return cls._workerPool

    @classmethod
    def getService(cls) -> TrainingService:
        if cls._service is None:
            cls._service = TrainingService(
                modelFactory=cls._defaultModelFactory,
                tokenizerRepo=cls.getTokenizerRepository(),
                checkpointRepo=cls.getCheckpointRepository(),
                corpusRepo=cls.getCorpusRepository(),
                jobRepo=cls.getJobRepository(),
                workerPool=cls.getWorkerPool(),
                defaultCheckpointDir=settings.checkpointDir,
            )
        return cls._service

    @staticmethod
    def _defaultModelFactory(config: ModelConfig) -> ModelRunner:
        """Build a runner; training runs on the fastest available device."""
        return ModelRunner(config)


@trainingBlueprint.route("/jobs", methods=["POST"])
@requireAuth
@validateInput(TrainingStartRequest)
def startTraining(validated: TrainingStartRequest, user: Any) -> Any:
    """Validate the payload and queue a training job."""
    config = validated.toConfig(
        checkpointDir=settings.checkpointDir,
        shardDir=TrainingContainer.getCorpusRepository().getShardDir(),
    )
    job = TrainingContainer.getService().startTraining(config, user.id)
    return jsonify(job.toDict()), 202


@trainingBlueprint.route("/jobs", methods=["GET"])
@requireAuth
def listTrainingJobs(user: Any) -> Any:
    """Return the most recent training jobs of the current user."""
    limit = _intArg("limit", default=50, minimum=1, maximum=200)
    jobs = TrainingContainer.getService().listJobs(user.id, limit=limit)
    return jsonify([job.toDict() for job in jobs])


@trainingBlueprint.route("/jobs/<jobId>", methods=["GET"])
@requireAuth
def getTrainingJob(user: Any, jobId: str) -> Any:
    """Return the current state of one training job."""
    job = TrainingContainer.getService().getJob(jobId, user.id)
    return jsonify(job.toDict())


@trainingBlueprint.route("/jobs/<jobId>/cancel", methods=["POST"])
@requireAuth
def cancelTraining(user: Any, jobId: str) -> Any:
    """Request cancellation of a training job."""
    job = TrainingContainer.getService().cancelTraining(jobId, user.id)
    return jsonify(job.toDict())


@trainingBlueprint.route("/jobs/<jobId>/resume", methods=["POST"])
@requireAuth
@validateInput(TrainingResumeRequest)
def resumeTraining(
    validated: TrainingResumeRequest,
    user: Any,
    jobId: str,
) -> Any:
    """Queue a new job that resumes from a previous checkpoint."""
    service = TrainingContainer.getService()
    previousJob = service.getJob(jobId, user.id)
    storedConfig = previousJob.config.get("trainingConfig")
    if not storedConfig:
        raise ValidationError(
            "Configuration du job introuvable",
            details={"jobId": jobId},
        )

    config = validated.applyTo(TrainingConfig.fromDict(storedConfig))
    checkpointId = validated.checkpointId or previousJob.config.get("resumeFrom")
    job = service.resumeTraining(checkpointId, config, user.id)
    return jsonify(job.toDict()), 202


@trainingBlueprint.route("/checkpoints", methods=["GET"])
@requireAuth
def listCheckpoints(user: Any) -> Any:
    """List indexed checkpoints, newest first."""
    limit = _intArg("limit", default=50, minimum=1, maximum=200)
    offset = _intArg("offset", default=0, minimum=0, maximum=1_000_000)
    modelName = request.args.get("modelName") or None
    checkpoints = TrainingContainer.getService().listCheckpoints(
        limit=limit,
        offset=offset,
        modelName=modelName,
    )
    return jsonify([checkpoint.toDict() for checkpoint in checkpoints])


@trainingBlueprint.route("/checkpoints/<checkpointId>", methods=["GET"])
@requireAuth
def getCheckpoint(user: Any, checkpointId: str) -> Any:
    """Return one checkpoint and its metadata."""
    checkpoint = TrainingContainer.getService().getCheckpoint(checkpointId)
    return jsonify(checkpoint.toDict())


@trainingBlueprint.route("/presets", methods=["GET"])
@requireAuth
def listPresets(user: Any) -> Any:
    """Return the built-in model architectures."""
    presets = TrainingContainer.getService().listPresets()
    return jsonify(
        [
            {
                "name": name,
                "parameters": config.nParams,
                "modelConfig": config.toDict(),
            }
            for name, config in sorted(presets.items())
        ]
    )


def _intArg(
    name: str,
    default: int,
    minimum: int,
    maximum: int | None = None,
) -> int:
    """Parse and bound an integer query parameter."""
    rawValue = request.args.get(name)
    if rawValue is None or rawValue == "":
        return default
    try:
        value = int(rawValue)
    except ValueError:
        raise ValidationError(
            f"Parametre {name} invalide",
            details={"value": rawValue},
        ) from None
    if value < minimum or (maximum is not None and value > maximum):
        raise ValidationError(
            f"Parametre {name} hors bornes",
            details={"value": value, "minimum": minimum, "maximum": maximum},
        )
    return value


__all__ = ["TrainingContainer", "trainingBlueprint"]
