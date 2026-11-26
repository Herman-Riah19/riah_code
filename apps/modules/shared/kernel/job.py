# apps/modules/shared/kernel/job.py
"""Job primitives shared by every long-running module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from threading import RLock
from typing import Any


class JobStatus(str, Enum):
    """Lifecycle states of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Kinds of long-running jobs handled by the platform."""

    DATA_PIPELINE = "data_pipeline"
    TOKENIZER_TRAINING = "tokenizer_training"
    CORPUS_ENCODING = "corpus_encoding"
    TRAINING = "training"
    INFERENCE = "inference"


@dataclass
class Job:
    """Mutable job tracked while a worker executes a pipeline."""

    id: str
    jobType: JobType
    status: JobStatus
    config: dict[str, Any]
    userId: str | None
    createdAt: datetime
    startedAt: datetime | None = None
    finishedAt: datetime | None = None
    progress: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    resumeFrom: str | None = None
    result: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        jobType: JobType,
        config: dict[str, Any],
        userId: str | None,
    ) -> Job:
        """Create a pending job with a generated identifier."""
        return cls(
            id=str(uuid.uuid4()),
            jobType=jobType,
            status=JobStatus.PENDING,
            config=config,
            userId=userId,
            createdAt=datetime.now(UTC),
        )

    def toDict(self) -> dict[str, Any]:
        """Serialize the job for API responses."""
        return {
            "id": self.id,
            "jobType": self.jobType.value,
            "status": self.status.value,
            "config": self.config,
            "userId": self.userId,
            "createdAt": self.createdAt.isoformat(),
            "startedAt": self.startedAt.isoformat() if self.startedAt else None,
            "finishedAt": self.finishedAt.isoformat() if self.finishedAt else None,
            "progress": self.progress,
            "error": self.error,
            "resumeFrom": self.resumeFrom,
            "result": self.result,
        }


class JobRepository:
    """Thread-safe in-memory job registry."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = RLock()

    def save(self, job: Job) -> None:
        """Insert or update a job."""
        with self._lock:
            self._jobs[job.id] = job

    def findById(self, jobId: str) -> Job | None:
        """Return a job by identifier, or None when unknown."""
        with self._lock:
            return self._jobs.get(jobId)

    def listAll(self, userId: str | None = None, limit: int = 50) -> list[Job]:
        """Return the most recent jobs, optionally scoped to one user."""
        if limit <= 0:
            return []
        with self._lock:
            jobs = [job for job in self._jobs.values() if userId is None or job.userId == userId]
        jobs.sort(key=lambda job: job.createdAt, reverse=True)
        return jobs[:limit]
