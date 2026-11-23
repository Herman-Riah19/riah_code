# apps/modules/shared/kernel/workerPool.py
"""Bounded thread pool used to run background jobs."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable


class WorkerPool:
    """Submit long-running callables to a bounded thread pool."""

    def __init__(self, maxWorkers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=maxWorkers,
            thread_name_prefix="riah-worker",
        )

    def submit(self, task: Callable[..., Any], *args: Any) -> Future[Any]:
        """Queue a task and return its future."""
        return self._executor.submit(task, *args)
