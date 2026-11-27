"""Learning-rate schedule tests for the training loop."""

from __future__ import annotations

from pathlib import Path

import pytest

from trainingLoopTestUtils import buildLoop


class TestLearningRateSchedule:
    """Warmup, cosine, constant and WSD multipliers."""

    @pytest.mark.parametrize("scheduler", ["cosine", "cosine_warmup", "constant", "wsd"])
    def test_scale_stays_within_bounds(self, tmp_path: Path, scheduler: str) -> None:
        loop = buildLoop(
            tmp_path / scheduler,
            maxSteps=10,
            scheduler=scheduler,
            warmupSteps=2,
            decaySteps=10,
            lr=1e-3,
            minLr=1e-4,
            maxEpochs=1,
        )

        for step in range(12):
            scale = loop.scheduler.lr_lambdas[0](step)
            assert 0 < scale <= 1.0

        loop.train()
        learningRate = loop.optimizer.param_groups[0]["lr"]
        assert 1e-4 <= learningRate <= 1e-3

    def test_warmup_is_linear(self, tmp_path: Path) -> None:
        loop = buildLoop(
            tmp_path,
            maxSteps=10,
            scheduler="cosine_warmup",
            warmupSteps=4,
            lr=1e-3,
        )

        lrScale = loop.scheduler.lr_lambdas[0]
        assert lrScale(0) == pytest.approx(0.25)
        assert lrScale(1) == pytest.approx(0.5)
        assert lrScale(3) == pytest.approx(1.0)

    def test_constant_schedule_never_decays(self, tmp_path: Path) -> None:
        loop = buildLoop(
            tmp_path,
            maxSteps=10,
            scheduler="constant",
            lr=1e-3,
            minLr=1e-4,
        )

        lrScale = loop.scheduler.lr_lambdas[0]
        assert lrScale(0) == 1.0
        assert lrScale(500) == 1.0

    def test_cosine_reaches_the_floor(self, tmp_path: Path) -> None:
        loop = buildLoop(
            tmp_path,
            maxSteps=10,
            scheduler="cosine",
            warmupSteps=0,
            decaySteps=10,
            lr=1e-3,
            minLr=1e-4,
        )

        assert loop.scheduler.lr_lambdas[0](10) == pytest.approx(0.1)

    def test_wsd_decays_at_the_end(self, tmp_path: Path) -> None:
        loop = buildLoop(
            tmp_path,
            maxSteps=100,
            scheduler="wsd",
            warmupSteps=5,
            lr=1e-3,
            minLr=1e-4,
        )

        lrScale = loop.scheduler.lr_lambdas[0]
        assert lrScale(50) == 1.0
        assert lrScale(99) < 0.2
