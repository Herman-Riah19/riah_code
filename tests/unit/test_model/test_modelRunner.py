# tests/unit/test_model/test_modelRunner.py
"""Tests for the high-level ModelRunner (device, generation, checkpoints)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import torch

from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.models.modelModel import Checkpoint, GenerationOptions

from tinyModel import tinyGenerationOptions, tinyModelConfig


class FakeTokenizer:
    """Minimal tokenizer stub returning the EOS id for every sequence."""

    def encode(self, text: str, addSpecialTokens: bool = False) -> list[int]:
        """Return the EOS token id whatever the input text."""
        return [0]

    def decode(self, tokenIds: list[int]) -> str:
        """Decode nothing (not used by these tests)."""
        return ""


def _zeroedRunner(config=None) -> ModelRunner:
    """Build a runner whose logits are all zero (deterministic argmax = 0)."""
    runner = ModelRunner(
        config or tinyModelConfig(),
        device=torch.device("cpu"),
    )
    for parameter in runner.model.parameters():
        parameter.data.zero_()
    return runner


class TestModelRunnerBasics:
    """Device handling and forward pass."""

    def test_forward_shape(self, tinyRunner, tinyConfig) -> None:
        tokenIds = torch.randint(0, tinyConfig.vocabSize, (2, 5))
        logits = tinyRunner.forward(tokenIds)
        assert logits.shape == (2, 5, tinyConfig.vocabSize)

    def test_cpu_falls_back_to_float32(self) -> None:
        runner = ModelRunner(
            tinyModelConfig(dtype="bf16"),
            device=torch.device("cpu"),
        )
        assert runner.dtype == torch.float32

    def test_num_parameters(self, tinyRunner) -> None:
        assert tinyRunner.numParameters() > 0

    def test_build_sampler_includes_eos_and_stop_sequences(self) -> None:
        runner = ModelRunner(
            tinyModelConfig(eosTokenId=3),
            device=torch.device("cpu"),
            tokenizer=FakeTokenizer(),
        )
        sampler = runner.buildSampler(GenerationOptions(stopSequences=["stop"]))
        assert 3 in sampler.stopTokenIds
        assert 0 in sampler.stopTokenIds

    def test_build_sampler_seeds_generator(self, tinyRunner) -> None:
        sampler = tinyRunner.buildSampler(GenerationOptions(seed=42))
        assert sampler.generator is not None


class TestGeneration:
    """Generation loops and stop conditions."""

    def test_stream_stops_on_eos(self) -> None:
        runner = _zeroedRunner(tinyModelConfig(eosTokenId=0))
        prompt = torch.randint(0, 64, (1, 2))
        tokens = list(
            runner.streamGenerate(prompt, tinyGenerationOptions(maxTokens=5))
        )
        assert tokens == [0]

    def test_stream_generates_up_to_max_tokens(self) -> None:
        runner = _zeroedRunner(tinyModelConfig(eosTokenId=63))
        prompt = torch.randint(0, 64, (1, 2))
        tokens = list(
            runner.streamGenerate(prompt, tinyGenerationOptions(maxTokens=5))
        )
        assert tokens == [0, 0, 0, 0, 0]

    def test_generate_returns_prompt_plus_tokens(self) -> None:
        runner = _zeroedRunner(tinyModelConfig(eosTokenId=63))
        prompt = torch.randint(0, 64, (1, 3))
        output = runner.generate(prompt, tinyGenerationOptions(maxTokens=4))
        assert output.shape == (1, 7)
        torch.testing.assert_close(output[:, :3], prompt)

    def test_generate_with_zero_max_tokens_returns_prompt(self, tinyRunner) -> None:
        prompt = torch.randint(0, 64, (1, 2))
        output = tinyRunner.generate(prompt, tinyGenerationOptions(maxTokens=0))
        torch.testing.assert_close(output, prompt)


class TestCheckpoints:
    """Save/load round-trips."""

    def test_save_writes_state_with_config(self, tinyRunner, tmp_path: Path) -> None:
        path = tinyRunner.saveCheckpoint(tmp_path / "ckpt.pt", step=3, epoch=1)
        assert path.is_file()
        state = torch.load(path, map_location="cpu", weights_only=False)
        assert state["step"] == 3
        assert state["epoch"] == 1
        assert state["modelConfig"]["vocabSize"] == 64
        assert "model" in state

    def test_load_restores_weights(self, tmp_path: Path) -> None:
        config = tinyModelConfig()
        source = ModelRunner(config, device=torch.device("cpu"))
        path = source.saveCheckpoint(tmp_path / "ckpt.pt", step=7, epoch=2)
        checkpoint = Checkpoint(
            id="ckpt",
            path=path,
            step=7,
            epoch=2,
            loss=1.0,
            modelConfig=config,
            createdAt=datetime.now(timezone.utc),
        )

        prompt = torch.randint(0, config.vocabSize, (1, 4))
        expected = source.forward(prompt)

        restored = ModelRunner(config, device=torch.device("cpu"))
        restored.loadCheckpoint(checkpoint)

        torch.testing.assert_close(restored.forward(prompt), expected)
