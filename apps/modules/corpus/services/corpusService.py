# apps/modules/corpus/services/corpusService.py
"""Corpus service - job lifecycle around the pipeline orchestrator."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ...shared.kernel.exceptions import ResourceNotFoundError
from ...shared.kernel.job import Job, JobRepository, JobStatus, JobType
from ...shared.kernel.workerPool import WorkerPool
from ..models.corpusModel import CorpusStats, PipelineConfig, PipelineResult
from ..pipelines.pipelineOrchestrator import PipelineOrchestrator
from ..repositories.corpusRepository import CorpusRepository


class CorpusService:
    """Expose corpus use cases to the HTTP layer."""

    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
        workerPool: WorkerPool,
        orchestratorFactory: Callable[[PipelineConfig], PipelineOrchestrator] | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._corpusRepo = corpusRepo
        self._jobRepo = jobRepo
        self._workerPool = workerPool
        self._orchestratorFactory = orchestratorFactory

    def startPipeline(self, config: PipelineConfig, userId: str) -> str:
        """Create a pending job, queue it and return its identifier."""
        job = Job.create(
            jobType=JobType.DATA_PIPELINE,
            config=self._serializeConfig(config),
            userId=userId,
        )
        self._jobRepo.save(job)
        self._workerPool.submit(self._runPipeline, job.id)
        return job.id

    def resumePipeline(self, jobId: str) -> Job:
        """Requeue an existing job from its last checkpoint."""
        job = self._jobRepo.findById(jobId)
        if job is None:
            raise ResourceNotFoundError("Job introuvable", details={"jobId": jobId})
        job.status = JobStatus.PENDING
        job.error = None
        self._jobRepo.save(job)
        self._workerPool.submit(self._runPipeline, job.id)
        return job

    def getStats(self) -> CorpusStats:
        """Return aggregated corpus statistics."""
        return self._corpusRepo.getGlobalStats()

    def _runPipeline(self, jobId: str) -> None:
        job = self._jobRepo.findById(jobId)
        if job is None:
            return

        job.status = JobStatus.RUNNING
        job.startedAt = datetime.now(UTC)
        self._jobRepo.save(job)
        try:
            config = self._configFromJob(job)
            orchestrator = (
                self._orchestratorFactory(config)
                if self._orchestratorFactory is not None
                else self._orchestrator
            )
            result = orchestrator.runFullPipeline(config)
            job.progress = self._resultToDict(result)
            job.status = JobStatus.COMPLETED
        except Exception as error:  # noqa: BLE001 - surface any failure to the job
            job.status = JobStatus.FAILED
            job.error = str(error)
        finally:
            job.finishedAt = datetime.now(UTC)
            self._jobRepo.save(job)

    @staticmethod
    def _serializeConfig(config: PipelineConfig) -> dict[str, Any]:
        return {
            "outputDir": str(config.outputDir),
            "shardSizeTokens": config.shardSizeTokens,
            "tokenizerPath": str(config.tokenizerPath),
            "numWorkers": config.numWorkers,
            "batchSize": config.batchSize,
            "resumeFromStep": config.resumeFromStep,
            "sources": list(config.sources),
            "languages": list(config.languages),
            "maxArticlesPerLang": config.maxArticlesPerLang,
        }

    @staticmethod
    def _configFromJob(job: Job) -> PipelineConfig:
        config = job.config
        return PipelineConfig(
            outputDir=Path(config["outputDir"]),
            shardSizeTokens=int(config["shardSizeTokens"]),
            tokenizerPath=Path(config["tokenizerPath"]),
            numWorkers=int(config["numWorkers"]),
            batchSize=int(config["batchSize"]),
            resumeFromStep=config.get("resumeFromStep"),
            sources=list(config.get("sources") or ["wikipedia"]),
            languages=list(config.get("languages") or ["fr"]),
            maxArticlesPerLang=int(config.get("maxArticlesPerLang") or 1000),
        )

    @staticmethod
    def _resultToDict(result: PipelineResult) -> dict[str, Any]:
        return {
            "documentsScraped": result.documentsScraped,
            "documentsCleaned": result.documentsCleaned,
            "documentsFiltered": result.documentsFiltered,
            "documentsDeduplicated": result.documentsDeduplicated,
            "documentsExported": result.documentsExported,
            "shardsWritten": result.shardsWritten,
            "totalTokens": result.totalTokens,
        }
