"""Tests for coordinated training and inference GPU access."""

from __future__ import annotations

import pytest

from apps.modules.model.services.gpuExecutionCoordinator import GPUExecutionCoordinator
from apps.modules.shared.kernel.exceptions import GPUResourceBusyError


class TestGPUExecutionCoordinator:
    """Verify inference fails fast while training owns the shared GPU."""

    def test_inference_is_rejected_during_training(self) -> None:
        coordinator = GPUExecutionCoordinator()

        with coordinator.training():
            with pytest.raises(GPUResourceBusyError):
                with coordinator.inference():
                    pass

    def test_inference_is_allowed_after_training_releases_the_gpu(self) -> None:
        coordinator = GPUExecutionCoordinator()

        with coordinator.training():
            pass

        with coordinator.inference():
            pass
