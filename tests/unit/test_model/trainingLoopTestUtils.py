"""Factories shared by CPU training-loop tests."""

from __future__ import annotations

from pathlib import Path

import torch
from tinyModel import tinyTrainingConfig
from tinyShards import writeTinyShard

from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.pipelines.trainingLoop import TrainingLoop
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository


def buildLoop(
    tmp_path: Path,
    *,
    valShards: list[Path] | None = None,
    checkpointRepo: CheckpointRepository | None = None,
    progressCallback=None,
    **overrides,
) -> TrainingLoop:
    """Build a CPU training loop over a tiny shard."""
    trainShard = writeTinyShard(tmp_path / "data", name="train.bin", seed=11)
    defaults = {
        "trainShards": [trainShard],
        "valShards": valShards or [],
        "checkpointDir": tmp_path / "checkpoints",
        "numWorkers": 0,
        "compileModel": False,
        "dtype": "fp32",
    }
    defaults.update(overrides)
    config = tinyTrainingConfig(**defaults)
    runner = ModelRunner(config.modelConfig, device=torch.device("cpu"))
    return TrainingLoop(
        config,
        runner,
        checkpointRepo=checkpointRepo,
        runId="test-run",
        progressCallback=progressCallback,
    )
