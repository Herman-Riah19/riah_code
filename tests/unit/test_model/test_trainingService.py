# tests/unit/test_model/test_trainingService.py
"""Tests for the training service - job lifecycle, resume and cancellation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import torch
from fakes import (
    DeferredWorkerPool,
    FakeTokenizer,
    FakeTokenizerRepository,
    InlineWorkerPool,
    cpuModelFactory,
)
from tinyModel import tinyModelConfig, tinyTrainingConfig
from tinyShards import writeTinyShard

from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.models.modelModel import (
    MODEL_PRESETS,
    Checkpoint,
    TrainingConfig,
)
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.model.services.gpuExecutionCoordinator import GPUExecutionCoordinator
from apps.modules.model.services.trainingService import TrainingService
from apps.modules.shared.kernel.exceptions import (
    CheckpointNotFoundError,
    InvalidJobStateError,
    ResourceNotFoundError,
    ValidationError,
)
from apps.modules.shared.kernel.job import JobRepository, JobStatus
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository


class TrainingFixture:
    """Bundle the service, its repositories and a ready-to-run config."""

    def __init__(
        self,
        tmp_path: Path,
        workerPool=None,
        modelFactory: Callable | None = None,
    ) -> None:
        self.tmpPath = tmp_path
        self.checkpointRepo = CheckpointRepository(tmp_path / "checkpoints")
        self.gpuCoordinator = GPUExecutionCoordinator()
        self.tokenizerRepo = TokenizerRepository(tmp_path / "tokenizer")
        self.corpusRepo = CorpusRepository(tmp_path / "corpus")
        self.jobRepo = JobRepository()
        self.trainShard = writeTinyShard(tmp_path / "data", name="train.bin", seed=11)
        self.valShard = writeTinyShard(tmp_path / "data", name="val.bin", seed=23)
        self.config = tinyTrainingConfig(
            trainShards=[self.trainShard],
            valShards=[self.valShard],
            checkpointDir=tmp_path / "runs",
            numWorkers=0,
            dtype="fp32",
            compileModel=False,
            maxSteps=2,
            evalInterval=1,
            checkpointInterval=1,
            logInterval=0,
        )
        self.service = TrainingService(
            modelFactory=modelFactory or cpuModelFactory,
            tokenizerRepo=self.tokenizerRepo,
            checkpointRepo=self.checkpointRepo,
            corpusRepo=self.corpusRepo,
            jobRepo=self.jobRepo,
            workerPool=workerPool or InlineWorkerPool(),
            gpuCoordinator=self.gpuCoordinator,
            defaultCheckpointDir=tmp_path / "runs",
        )


@pytest.fixture
def fixture(tmp_path: Path) -> TrainingFixture:
    """Default fixture with an inline worker pool."""
    return TrainingFixture(tmp_path)


class TestTrainingJobLifecycle:
    """Start, inspect and finish training jobs."""

    def test_training_model_vocabulary_covers_the_installed_tokenizer(
        self, fixture: TrainingFixture
    ) -> None:
        class WideTokenizer(FakeTokenizer):
            vocabSize = 32_000
            eosTokenId = 17
            padTokenId = 19

        pool = DeferredWorkerPool()
        service = buildService(
            fixture,
            tokenizerRepo=FakeTokenizerRepository(tokenizer=WideTokenizer()),
            workerPool=pool,
        )

        job = service.startTraining(fixture.config, "user-1")

        task, args = pool.tasks[0]
        task(*args)
        completedJob = fixture.jobRepo.findById(job.id)

        assert completedJob is not None
        assert completedJob.config["trainingConfig"]["modelConfig"]["vocabSize"] == 32_000
        assert completedJob.config["trainingConfig"]["modelConfig"]["eosTokenId"] == 17
        assert completedJob.config["trainingConfig"]["modelConfig"]["padTokenId"] == 19

    def test_start_training_completes(self, fixture: TrainingFixture) -> None:
        job = fixture.service.startTraining(fixture.config, "user-1")

        assert job.status is JobStatus.COMPLETED
        assert job.result is not None
        assert job.result["steps"] == 2
        assert job.result["cancelled"] is False
        assert Path(job.result["finalCheckpoint"]).is_file()

    def test_each_run_gets_its_own_checkpoint_directory(self, fixture: TrainingFixture) -> None:
        job = fixture.service.startTraining(fixture.config, "user-1")

        checkpointDir = Path(job.result["checkpointDir"])
        assert checkpointDir.name == job.id
        assert checkpointDir.is_dir()

    def test_job_config_is_persisted(self, fixture: TrainingFixture) -> None:
        job = fixture.service.startTraining(fixture.config, "user-1")

        assert job.config["runId"] == job.id
        assert job.config["modelName"] == "default"
        stored = TrainingConfig.fromDict(job.config["trainingConfig"])
        assert stored.seqLen == fixture.config.seqLen
        assert stored.trainShards == [fixture.trainShard.resolve()]

    def test_progress_is_populated_after_completion(self, fixture: TrainingFixture) -> None:
        job = fixture.service.startTraining(fixture.config, "user-1")

        assert job.progress["step"] == 2
        assert job.progress["maxSteps"] == 2
        assert job.progress["progress"] == 1.0

    def test_get_job_scopes_to_the_owner(self, fixture: TrainingFixture) -> None:
        job = fixture.service.startTraining(fixture.config, "user-1")

        assert fixture.service.getJob(job.id, "user-1") is job
        with pytest.raises(ResourceNotFoundError):
            fixture.service.getJob(job.id, "user-2")
        with pytest.raises(ResourceNotFoundError):
            fixture.service.getJob("unknown", "user-1")

    def test_list_jobs_returns_recent_first(self, fixture: TrainingFixture) -> None:
        first = fixture.service.startTraining(fixture.config, "user-1")
        second = fixture.service.startTraining(fixture.config, "user-1")

        jobs = fixture.service.listJobs("user-1", limit=5)

        assert jobs[0].id == second.id
        assert jobs[1].id == first.id
        assert fixture.service.listJobs("user-2") == []

    def test_list_checkpoints_and_get_one(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")
        latest = fixture.checkpointRepo.findLatest()
        assert latest is not None

        checkpoints = fixture.service.listCheckpoints(limit=10)

        assert checkpoints
        assert fixture.service.getCheckpoint(latest.id).id == latest.id
        with pytest.raises(CheckpointNotFoundError):
            fixture.service.getCheckpoint("missing")

    def test_list_presets(self) -> None:
        presets = TrainingService.listPresets()
        assert "tiny" in presets
        assert presets["tiny"].dim == 64


class TestTrainingResume:
    """Resume from explicit or latest checkpoints."""

    def test_resume_from_checkpoint(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")
        latest = fixture.checkpointRepo.findLatest()
        assert latest is not None

        job = fixture.service.resumeTraining(
            latest.id,
            replace(fixture.config, maxSteps=3),
            "user-1",
        )

        assert job.status is JobStatus.COMPLETED
        assert job.resumeFrom == latest.id
        assert job.result is not None
        assert job.result["steps"] == 3
        assert Path(job.result["checkpointDir"]) == latest.path.parent

    def test_resume_without_id_uses_latest_checkpoint(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")
        latest = fixture.checkpointRepo.findLatest()
        assert latest is not None

        job = fixture.service.resumeTraining(None, fixture.config, "user-1")

        assert job.status is JobStatus.COMPLETED
        assert job.resumeFrom == latest.id

    def test_resume_unknown_checkpoint_raises(self, fixture: TrainingFixture) -> None:
        with pytest.raises(CheckpointNotFoundError):
            fixture.service.resumeTraining("missing", fixture.config, "user-1")

    def test_resume_without_any_checkpoint_raises(self, fixture: TrainingFixture) -> None:
        with pytest.raises(CheckpointNotFoundError, match="Aucun checkpoint"):
            fixture.service.resumeTraining(None, fixture.config, "user-1")

    def test_resume_requires_a_training_config(self, fixture: TrainingFixture) -> None:
        checkpoint = Checkpoint(
            id="manual",
            path=fixture.tmpPath / "manual.pt",
            step=0,
            epoch=0,
            loss=1.0,
            modelConfig=tinyModelConfig(),
            trainingConfig=None,
            createdAt=datetime.now(UTC),
        )
        fixture.checkpointRepo.save(checkpoint)

        with pytest.raises(ValidationError, match="Configuration"):
            fixture.service.resumeTraining("manual", None, "user-1")

    def test_resume_uses_checkpoint_config_when_omitted(self, fixture: TrainingFixture) -> None:
        firstJob = fixture.service.startTraining(fixture.config, "user-1")
        latest = fixture.checkpointRepo.findLatest()
        assert latest is not None

        job = fixture.service.resumeTraining(latest.id, None, "user-1")

        assert job.status is JobStatus.COMPLETED
        assert job.result is not None
        assert job.result["steps"] == firstJob.result["steps"]


class TestTrainingCancellation:
    """Pending and running cancellation paths."""

    def test_cancel_pending_job(self, tmp_path: Path) -> None:
        pool = DeferredWorkerPool()
        fixture = TrainingFixture(tmp_path, workerPool=pool)

        job = fixture.service.startTraining(fixture.config, "user-1")
        assert job.status is JobStatus.PENDING
        assert len(pool.tasks) == 1

        cancelled = fixture.service.cancelTraining(job.id, "user-1")

        task, args = pool.tasks[0]
        task(*args)

        assert cancelled.status is JobStatus.CANCELLED
        assert cancelled.finishedAt is not None
        assert cancelled.progress["cancelRequested"] is True
        assert fixture.jobRepo.findById(job.id).status is JobStatus.CANCELLED

    def test_cancel_completed_job_raises(self, fixture: TrainingFixture) -> None:
        job = fixture.service.startTraining(fixture.config, "user-1")

        with pytest.raises(InvalidJobStateError):
            fixture.service.cancelTraining(job.id, "user-1")

    def test_cancel_unknown_job_raises(self, fixture: TrainingFixture) -> None:
        with pytest.raises(ResourceNotFoundError):
            fixture.service.cancelTraining("unknown", "user-1")


class TestTrainingFailures:
    """Failure paths are surfaced on the job."""

    def test_invalid_shard_marks_job_failed(self, fixture: TrainingFixture) -> None:
        config = replace(
            fixture.config,
            trainShards=[fixture.tmpPath / "missing.bin"],
        )

        job = fixture.service.startTraining(config, "user-1")

        assert job.status is JobStatus.FAILED
        assert job.error is not None
        assert "Shard introuvable" in job.error
        assert job.finishedAt is not None

    def test_missing_shards_raise_before_queueing(self, fixture: TrainingFixture) -> None:
        config = replace(fixture.config, trainShards=[], valShards=[])

        with pytest.raises(ValidationError, match="Aucun shard"):
            fixture.service.startTraining(config, "user-1")

    def test_corpus_directory_is_used_as_fallback(self, fixture: TrainingFixture) -> None:
        fallbackShard = writeTinyShard(
            fixture.corpusRepo.getShardDir(),
            name="shard_000001.bin",
            seed=31,
        )
        config = replace(fixture.config, trainShards=[], valShards=[])

        job = fixture.service.startTraining(config, "user-1")

        assert job.status is JobStatus.COMPLETED
        stored = TrainingConfig.fromDict(job.config["trainingConfig"])
        assert stored.trainShards == [fallbackShard.resolve()]

    def test_missing_tokenizer_is_tolerated(self, fixture: TrainingFixture) -> None:
        assert not fixture.tokenizerRepo.exists()
        job = fixture.service.startTraining(fixture.config, "user-1")
        assert job.status is JobStatus.COMPLETED

    def test_compile_flag_sets_the_model_compile_mode(self, tmp_path: Path) -> None:
        recorded: list[Any] = []

        def factory(modelConfig):
            recorded.append(modelConfig)
            return ModelRunner(
                replace(modelConfig, compileMode=None),
                device=torch.device("cpu"),
            )

        fixture = TrainingFixture(tmp_path, modelFactory=factory)
        job = fixture.service.startTraining(
            replace(fixture.config, compileModel=True, maxSteps=1),
            "user-1",
        )

        assert job.status is JobStatus.COMPLETED
        assert recorded[0].compileMode == "default"


class FakeLoop:
    """Minimal loop used to exercise the running-cancellation branch."""

    def __init__(self) -> None:
        self.cancelCalls = 0
        self.cancelled = False

    def cancel(self) -> None:
        """Record the cancellation request."""
        self.cancelCalls += 1


class BrokenTokenizerRepository:
    """Tokenizer repository whose persisted tokenizer is corrupted."""

    tokenizerPath = Path("broken/tokenizer.json")

    def exists(self) -> bool:
        """The broken tokenizer is reported as present."""
        return True

    def load(self) -> None:
        """Fail like a corrupted tokenizer file would."""
        raise RuntimeError("tokenizer corrompu")


def buildService(
    fixture: TrainingFixture,
    *,
    tokenizerRepo=None,
    workerPool=None,
) -> TrainingService:
    """Build a second service sharing the fixture repositories."""
    return TrainingService(
        modelFactory=cpuModelFactory,
        tokenizerRepo=tokenizerRepo or fixture.tokenizerRepo,
        checkpointRepo=fixture.checkpointRepo,
        corpusRepo=fixture.corpusRepo,
        jobRepo=fixture.jobRepo,
        workerPool=workerPool or InlineWorkerPool(),
        gpuCoordinator=fixture.gpuCoordinator,
        defaultCheckpointDir=fixture.tmpPath / "runs",
    )


class TestTrainingQueries:
    """Listing and validation of the service read paths."""

    def test_list_jobs_with_zero_limit(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")

        assert fixture.service.listJobs("user-1", limit=0) == []

    def test_list_checkpoints_filters_by_model_name(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")

        assert fixture.service.listCheckpoints(modelName="default")
        assert fixture.service.listCheckpoints(modelName="other") == []

    def test_list_checkpoints_applies_the_offset(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")
        everyCheckpoint = fixture.service.listCheckpoints(limit=20)
        assert len(everyCheckpoint) >= 2

        assert fixture.service.listCheckpoints(limit=20, offset=1) == everyCheckpoint[1:]

    def test_list_presets_contains_every_builtin(self) -> None:
        assert set(TrainingService.listPresets()) == set(MODEL_PRESETS)

    def test_each_run_gets_a_distinct_directory(self, fixture: TrainingFixture) -> None:
        first = fixture.service.startTraining(fixture.config, "user-1")
        second = fixture.service.startTraining(fixture.config, "user-1")

        assert first.result["checkpointDir"] != second.result["checkpointDir"]

    def test_config_directory_is_used_without_a_default(self, fixture: TrainingFixture) -> None:
        service = TrainingService(
            modelFactory=cpuModelFactory,
            tokenizerRepo=fixture.tokenizerRepo,
            checkpointRepo=fixture.checkpointRepo,
            corpusRepo=fixture.corpusRepo,
            jobRepo=fixture.jobRepo,
            workerPool=InlineWorkerPool(),
            gpuCoordinator=fixture.gpuCoordinator,
            defaultCheckpointDir=None,
        )

        job = service.startTraining(fixture.config, "user-1")

        assert Path(job.result["checkpointDir"]) == (fixture.config.checkpointDir / job.id)


class TestTrainingCancellationBranches:
    """Cancellation of a job that is already running."""

    def test_cancel_running_job_asks_the_loop_to_stop(self, tmp_path: Path) -> None:
        pool = DeferredWorkerPool()
        fixture = TrainingFixture(tmp_path, workerPool=pool)
        job = fixture.service.startTraining(fixture.config, "user-1")
        job.status = JobStatus.RUNNING
        loop = FakeLoop()
        fixture.service._loops[job.id] = loop  # type: ignore[assignment]

        cancelled = fixture.service.cancelTraining(job.id, "user-1")

        assert loop.cancelCalls == 1
        assert cancelled.status is JobStatus.RUNNING
        assert cancelled.progress["cancelRequested"] is True
        assert cancelled.finishedAt is None


class TestTrainingFailureModes:
    """Failures raised by collaborators must surface on the job."""

    def test_corrupted_tokenizer_marks_the_job_failed(self, fixture: TrainingFixture) -> None:
        service = buildService(
            fixture,
            tokenizerRepo=BrokenTokenizerRepository(),
        )

        job = service.startTraining(fixture.config, "user-1")

        assert job.status is JobStatus.FAILED
        assert job.error is not None
        assert "corrompu" in job.error

    def test_resume_records_the_source_checkpoint(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")
        latest = fixture.checkpointRepo.findLatest()
        assert latest is not None

        job = fixture.service.resumeTraining(latest.id, None, "user-1")

        assert job.config["resumeFrom"] == latest.id
        assert job.config["runId"] == job.id

    def test_resume_with_explicit_config_extends_training(self, fixture: TrainingFixture) -> None:
        fixture.service.startTraining(fixture.config, "user-1")
        latest = fixture.checkpointRepo.findLatest()
        assert latest is not None

        job = fixture.service.resumeTraining(
            latest.id,
            replace(fixture.config, maxSteps=4),
            "user-1",
        )

        assert job.result is not None
        assert job.result["steps"] == 4
