"""Coordinate training and inference access to the shared GPU."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from apps.modules.shared.kernel.exceptions import GPUResourceBusyError


class GPUExecutionCoordinator:
    """Serialize training and inference work using the process GPU."""

    def __init__(self) -> None:
        self._lock = Lock()

    @contextmanager
    def training(self) -> Iterator[None]:
        """Wait for active inference and reserve the GPU for a training run."""
        with self._lock:
            yield

    @contextmanager
    def inference(self) -> Iterator[None]:
        """Reserve an idle GPU for inference or raise instead of waiting."""
        if not self._lock.acquire(blocking=False):
            raise GPUResourceBusyError(
                "Le GPU est occupe par un entrainement ou une autre requete",
                details={"resource": "gpu"},
            )
        try:
            yield
        finally:
            self._lock.release()


gpuExecutionCoordinator = GPUExecutionCoordinator()

__all__ = ["GPUExecutionCoordinator", "gpuExecutionCoordinator"]
