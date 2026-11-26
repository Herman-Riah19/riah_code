# apps/modules/model/services/trainingService.py
"""Training service - job lifecycle for training and resume runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, Any

from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.kernel.exceptions import (
    CheckpointNotFoundError,
    InvalidJobStateError,
    ResourceNotFoundError,
    TokenizerNotFoundError,
    ValidationError,
)
from apps.modules.shared.kernel.job import Job, JobRepository, JobStatus, JobType
from apps.modules.shared.kernel.workerPool import WorkerPool
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository

from ..ml.modelRunner import ModelRunner
from ..models.modelModel import (
    MODEL_PRESETS,
    Checkpoint,
    ModelConfig,
    TrainingConfig,
    TrainingResult,
)
from ..pipelines.trainingLoop import TrainingLoop
from ..repositories.checkpointRepository import CheckpointRepository

if TYPE_CHECKING:  # pragma: no cover - typing only
    from apps.modules.tokenizer.models.tokenizerModel import BPETokenizer

ModelFactory = Callable[[ModelConfig], ModelRunner]
ProgressHandler = Callable[[dict[str, Any]], None]


class TrainingService:
    """Expose training use cases to the HTTP layer and to the CLI."""

    def __init__(
        self,
        modelFactory: ModelFactory,
        tokenizerRepo: TokenizerRepository,
        checkpointRepo: CheckpointRepository,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
        workerPool: WorkerPool,
        defaultCheckpointDir: Path | None = None,
    ) -> None:
        self._modelFactory = modelFactory
        self._tokenizerRepo = tokenizerRepo
        self._checkpointRepo = checkpointRepo
        self._corpusRepo = corpusRepo
        self._jobRepo = jobRepo
        self._workerPool = workerPool
        self._defaultCheckpointDir = defaultCheckpointDir
        self._loops: dict[str, TrainingLoop] = {}
        self._lock = RLock()

    # ----------------------------------------------------------------- public

    def startTraining(self, config: TrainingConfig, userId: str) -> Job:
        """Create, queue and return a new training job."""
        resolvedConfig = self._ensureTrainShards(config)
        job = Job.create(jobType=JobType.TRAINING, config={}, userId=userId)
        runConfig = replace(
            resolvedConfig,
            checkpointDir=self._runDirectory(resolvedConfig, job.id),
        )
        job.config = self._serializeJobConfig(runConfig, job.id)
        self._jobRepo.save(job)
        self._workerPool.submit(self._runTraining, job.id, runConfig, None)
        return job

    def resumeTraining(
        self,
        checkpointId: str | None,
        config: TrainingConfig | None,
        userId: str,
    ) -> Job:
        """Create a job that resumes training from a checkpoint."""
        checkpoint = self._resolveCheckpoint(checkpointId, config)
        resolvedConfig = config or checkpoint.trainingConfig
        if resolvedConfig is None:
            raise ValidationError(
                "Configuration d'entrainement absente du checkpoint",
                details={"checkpointId": checkpoint.id},
            )

        runConfig = replace(
            resolvedConfig,
            checkpointDir=checkpoint.path.parent,
        )
        job = Job.create(jobType=JobType.TRAINING, config={}, userId=userId)
        job.resumeFrom = checkpoint.id
        job.config = self._serializeJobConfig(runConfig, job.id)
        job.config["resumeFrom"] = checkpoint.id
        self._jobRepo.save(job)
        self._workerPool.submit(self._runTraining, job.id, runConfig, checkpoint.id)
        return job

    def cancelTraining(self, jobId: str, userId: str) -> Job:
        """Request cancellation of a pending or running training job."""
        job = self.getJob(jobId, userId)
        with self._lock:
            loop = self._loops.get(jobId)

        if loop is not None:
            loop.cancel()
            job.progress = {**job.progress, "cancelRequested": True}
        elif job.status is JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            job.progress = {**job.progress, "cancelRequested": True}
            job.finishedAt = datetime.now(UTC)
        else:
            raise InvalidJobStateError(
                "Ce job ne peut plus etre annule",
                details={"jobId": jobId, "status": job.status.value},
            )

        self._jobRepo.save(job)
        return job

    def getJob(self, jobId: str, userId: str) -> Job:
        """Return one job owned by the user, or raise when unknown."""
        job = self._jobRepo.findById(jobId)
        if job is None or job.userId != userId:
            raise ResourceNotFoundError("Job introuvable", details={"jobId": jobId})
        return job

    def listJobs(self, userId: str, limit: int = 50) -> list[Job]:
        """Return the most recent jobs of one user."""
        return self._jobRepo.listAll(userId=userId, limit=limit)

    def listCheckpoints(
        self,
        limit: int = 50,
        offset: int = 0,
        modelName: str | None = None,
    ) -> list[Checkpoint]:
        """Return indexed checkpoints, newest first."""
        return self._checkpointRepo.listAll(
            limit=limit,
            offset=offset,
            modelName=modelName,
        )

    def getCheckpoint(self, checkpointId: str) -> Checkpoint:
        """Return one checkpoint or raise `CheckpointNotFoundError`."""
        checkpoint = self._checkpointRepo.findById(checkpointId)
        if checkpoint is None:
            raise CheckpointNotFoundError(
                "Checkpoint introuvable",
                details={"checkpointId": checkpointId},
            )
        return checkpoint

    @staticmethod
    def listPresets() -> dict[str, ModelConfig]:
        """Return the built-in architecture presets."""
        return dict(MODEL_PRESETS)

    # --------------------------------------------------------------- internals

    def _buildRunner(self, config: TrainingConfig) -> ModelRunner:
        """Build the runner, honouring `compileModel` on the model config."""
        modelConfig = config.modelConfig
        if config.compileModel and modelConfig.compileMode is None:
            modelConfig = replace(modelConfig, compileMode="default")
        return self._modelFactory(modelConfig)

    def _runTraining(
        self,
        jobId: str,
        config: TrainingConfig,
        resumeFrom: str | None,
    ) -> None:
        """Worker entry point: train, resume and record the outcome."""
        job = self._startJob(jobId)
        if job is None:
            return

        loop: TrainingLoop | None = None
        try:
            runner = self._buildRunner(config)
            loop = TrainingLoop(
                config=config,
                modelRunner=runner,
                tokenizer=self._loadTokenizer(),
                checkpointRepo=self._checkpointRepo,
                runId=jobId,
                progressCallback=self._buildProgressHandler(jobId),
            )
            if resumeFrom is not None:
                loop.loadCheckpoint(self._checkpointRepo.requireById(resumeFrom))

            with self._lock:
                self._loops[jobId] = loop

            result = loop.train()
            job.progress = loop.snapshot()
            job.status = JobStatus.CANCELLED if loop.cancelled else JobStatus.COMPLETED
            job.result = self._buildResult(result, config, loop.cancelled)
        except Exception as error:  # noqa: BLE001 - surface any failure to the job
            job.status = JobStatus.FAILED
            job.error = str(error)
        finally:
            with self._lock:
                self._loops.pop(jobId, None)
            job.finishedAt = datetime.now(UTC)
            self._jobRepo.save(job)

    @staticmethod
    def _buildResult(
        result: TrainingResult,
        config: TrainingConfig,
        cancelled: bool,
    ) -> dict[str, Any]:
        """Shape the final job result payload."""
        tag = "cancelled" if cancelled else "final"
        finalPath = Path(config.checkpointDir) / f"checkpoint_{tag}.pt"
        return {
            **result.toDict(),
            "checkpointDir": str(config.checkpointDir),
            "finalCheckpoint": str(finalPath),
            "cancelled": cancelled,
        }

    def _resolveCheckpoint(
        self,
        checkpointId: str | None,
        config: TrainingConfig | None,
    ) -> Checkpoint:
        """Resolve an explicit checkpoint id or the latest one of a model."""
        if checkpointId:
            checkpoint = self._checkpointRepo.findById(checkpointId)
            if checkpoint is None:
                raise CheckpointNotFoundError(
                    "Checkpoint introuvable",
                    details={"checkpointId": checkpointId},
                )
            return checkpoint

        modelName = config.modelName if config is not None else None
        checkpoint = self._checkpointRepo.findLatest(modelName=modelName)
        if checkpoint is None:
            raise CheckpointNotFoundError(
                "Aucun checkpoint disponible pour la reprise",
                details={"modelName": modelName},
            )
        return checkpoint

    def _buildProgressHandler(self, jobId: str) -> ProgressHandler:
        """Return a callback that mirrors loop snapshots into the job."""

        def handler(snapshot: dict[str, Any]) -> None:
            job = self._jobRepo.findById(jobId)
            if job is None:
                return
            job.progress = snapshot
            self._jobRepo.save(job)

        return handler

    def _ensureTrainShards(self, config: TrainingConfig) -> TrainingConfig:
        """Fall back to the corpus shard directory when no shard is given."""
        if config.trainShards:
            return config

        shardDir = self._corpusRepo.getShardDir()
        shards = sorted(shardDir.glob("shard_*.bin"))
        if not shards:
            raise ValidationError(
                "Aucun shard d'entrainement disponible",
                details={"shardDir": str(shardDir)},
            )
        return replace(config, trainShards=shards)

    def _runDirectory(self, config: TrainingConfig, jobId: str) -> Path:
        """Give every run its own checkpoint directory."""
        baseDir = self._defaultCheckpointDir or config.checkpointDir
        return Path(baseDir) / jobId

    def _loadTokenizer(self) -> BPETokenizer | None:
        """Load the tokenizer when available; training does not require it."""
        try:
            tokenizer, _ = self._tokenizerRepo.load()
        except TokenizerNotFoundError:
            return None
        return tokenizer

    @staticmethod
    def _serializeJobConfig(config: TrainingConfig, runId: str) -> dict[str, Any]:
        """Store the resolved config in the job for later resume/UI calls."""
        return {
            "trainingConfig": config.toDict(),
            "modelName": config.modelName,
            "runId": runId,
        }

    def _startJob(self, jobId: str) -> Job | None:
        """Mark a job as running and persist the transition."""
        job = self._jobRepo.findById(jobId)
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.startedAt = datetime.now(UTC)
        job.error = None
        self._jobRepo.save(job)
        return job


__all__ = ["ModelFactory", "TrainingService"]
