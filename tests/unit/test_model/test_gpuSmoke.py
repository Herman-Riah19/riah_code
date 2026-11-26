# tests/unit/test_model/test_gpuSmoke.py
"""GPU smoke tests - skipped automatically when no CUDA device is present."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
from tinyModel import tinyGenerationOptions, tinyModelConfig, tinyTrainingConfig
from tinyShards import writeTinyShard

from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.pipelines.trainingLoop import TrainingLoop
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository

pytestmark = [
    pytest.mark.gpu,
    pytest.mark.skipif(
        not torch.cuda.is_available(),
        reason="CUDA indisponible sur cette machine",
    ),
]


@pytest.fixture
def cudaDevice() -> torch.device:
    """Return the default CUDA device."""
    return torch.device("cuda")


class TestCudaRunner:
    """ModelRunner precision and generation on CUDA."""

    def test_bf16_forward_returns_bf16_logits(self, cudaDevice: torch.device) -> None:
        runner = ModelRunner(tinyModelConfig(dtype="bf16"), device=cudaDevice)
        inputIds = torch.randint(0, 64, (2, 8))

        logits = runner.forward(inputIds)

        assert runner.device.type == "cuda"
        assert runner.dtype is torch.bfloat16
        assert logits.device.type == "cuda"
        assert logits.dtype is torch.bfloat16
        assert logits.shape == (2, 8, 64)

    def test_generation_keeps_the_prompt_on_cuda(self, cudaDevice: torch.device) -> None:
        runner = ModelRunner(tinyModelConfig(eosTokenId=63), device=cudaDevice)
        for parameter in runner.model.parameters():
            parameter.data.zero_()
        inputIds = torch.tensor([[1, 2, 3]], dtype=torch.long)

        output = runner.generate(inputIds, tinyGenerationOptions(maxTokens=3))

        assert output.device.type == "cuda"
        assert output.shape == (1, 6)
        assert output[0, :3].tolist() == [1, 2, 3]

    def test_cpu_falls_back_to_fp32(self) -> None:
        runner = ModelRunner(tinyModelConfig(dtype="fp16"), device=torch.device("cpu"))
        assert runner.dtype is torch.float32


class TestCudaTraining:
    """One-step training runs on the GPU with mixed precision."""

    def test_bf16_training_step(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path / "data", seed=11)
        config = tinyTrainingConfig(
            modelConfig=tinyModelConfig(dtype="bf16"),
            trainShards=[shard],
            checkpointDir=tmp_path / "checkpoints",
            numWorkers=0,
            compileModel=False,
            dtype="bf16",
            maxSteps=1,
            evalInterval=0,
            checkpointInterval=0,
            logInterval=0,
        )
        runner = ModelRunner(config.modelConfig, device=torch.device("cuda"))
        repository = CheckpointRepository(tmp_path / "index")
        loop = TrainingLoop(config, runner, checkpointRepo=repository, runId="gpu-run")

        result = loop.train()

        assert loop.device.type == "cuda"
        assert result.steps == 1
        assert result.finalLoss is not None
        assert torch.isfinite(torch.tensor(result.finalLoss))
        assert repository.findLatest() is not None

    def test_fp16_enables_the_grad_scaler(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path / "data", seed=11)
        config = tinyTrainingConfig(
            modelConfig=tinyModelConfig(dtype="fp16"),
            trainShards=[shard],
            checkpointDir=tmp_path / "checkpoints",
            numWorkers=0,
            compileModel=False,
            dtype="fp16",
            useGradScaler=True,
            maxSteps=1,
        )
        runner = ModelRunner(config.modelConfig, device=torch.device("cuda"))

        loop = TrainingLoop(config, runner)

        assert loop.scaler.is_enabled() is True
        assert loop.train().steps == 1

    def test_fp32_disables_the_grad_scaler(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path / "data", seed=11)
        config = tinyTrainingConfig(
            trainShards=[shard],
            checkpointDir=tmp_path / "checkpoints",
            numWorkers=0,
            dtype="fp32",
            maxSteps=1,
        )
        runner = ModelRunner(config.modelConfig, device=torch.device("cuda"))

        loop = TrainingLoop(config, runner)

        assert loop.scaler.is_enabled() is False
