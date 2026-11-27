# tests/unit/test_model/test_modelModel.py
"""Tests for the model domain dataclasses."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from tinyModel import tinyModelConfig, tinyTrainingConfig

from apps.modules.model.models.modelModel import (
    MODEL_PRESETS,
    Checkpoint,
    GenerationOptions,
    ModelConfig,
    TrainingConfig,
    TrainingResult,
)


class TestModelConfig:
    """Architecture config validation and serialization."""

    def test_presets_expose_expected_scale(self) -> None:
        assert {"tiny", "125M", "350M", "760M", "1.3B"} <= set(MODEL_PRESETS)
        assert MODEL_PRESETS["125M"].dim == 768
        assert MODEL_PRESETS["1.3B"].dim == 2048

    def test_parameter_count_is_positive_and_grows(self) -> None:
        small = tinyModelConfig(dim=16)
        large = tinyModelConfig(dim=32)
        assert small.nParams > 0
        assert large.nParams > small.nParams

    def test_head_dim_rejects_indivisible_dim(self) -> None:
        with pytest.raises(ValueError, match="divisible"):
            _ = tinyModelConfig(dim=15, nHeads=2).headDim

    def test_resolved_defaults(self) -> None:
        config = tinyModelConfig(dim=16, nHeads=2, dimFF=None, nKvHeads=None)
        assert config.resolvedDimFF == 64
        assert config.resolvedKvHeads == 2
        assert config.headDim == 8

    def test_dict_round_trip(self) -> None:
        config = tinyModelConfig(nKvHeads=1, ropeScaling={"factor": 2.0})
        restored = ModelConfig.fromDict(config.toDict())
        assert restored == config

    def test_from_dict_ignores_unknown_keys(self) -> None:
        payload = tinyModelConfig().toDict()
        payload["legacyField"] = True
        assert ModelConfig.fromDict(payload) == tinyModelConfig()


class TestTrainingConfig:
    """Training config helpers and serialization."""

    def test_effective_batch_size_includes_accumulation(self) -> None:
        config = tinyTrainingConfig(batchSize=4, gradientAccumulationSteps=3)
        assert config.effectiveBatchSize == 12

    def test_effective_batch_size_uses_micro_batch_size_when_configured(self) -> None:
        config = tinyTrainingConfig(
            batchSize=8,
            microBatchSize=2,
            gradientAccumulationSteps=3,
        )
        assert config.effectiveBatchSize == 6

    def test_dict_round_trip_with_paths(self) -> None:
        config = tinyTrainingConfig(
            trainShards=[Path("data/shards/train_000.bin")],
            valShards=[Path("data/shards/val_000.bin")],
            checkpointDir=Path("data/checkpoints"),
        )
        restored = TrainingConfig.fromDict(config.toDict())
        assert restored == config

    def test_model_config_survives_nested_round_trip(self) -> None:
        config = tinyTrainingConfig(modelConfig=tinyModelConfig(nKvHeads=1))
        restored = TrainingConfig.fromDict(config.toDict())
        assert restored.modelConfig == config.modelConfig


class TestCheckpoint:
    """Checkpoint metadata serialization."""

    def test_dict_round_trip(self) -> None:
        created = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)
        checkpoint = Checkpoint(
            id="ckpt-1",
            path=Path("data/checkpoints/ckpt-1.pt"),
            step=120,
            epoch=2,
            loss=1.25,
            valLoss=1.1,
            modelConfig=tinyModelConfig(),
            trainingConfig=tinyTrainingConfig(),
            createdAt=created,
            isBest=True,
            modelName="tiny-model",
            metadata={"note": "unit"},
        )

        restored = Checkpoint.fromDict(checkpoint.toDict())

        assert restored == checkpoint

    def test_val_loss_is_optional(self) -> None:
        checkpoint = Checkpoint(
            id="ckpt-2",
            path=Path("ckpt-2.pt"),
            step=1,
            epoch=0,
            loss=2.0,
            modelConfig=tinyModelConfig(),
            createdAt=datetime.now(UTC),
        )
        assert Checkpoint.fromDict(checkpoint.toDict()).valLoss is None


class TestGenerationOptions:
    """Sampling option defaults."""

    def test_defaults(self) -> None:
        options = GenerationOptions()
        assert options.maxTokens == 128
        assert options.topK == 50
        assert options.stopSequences == []

    def test_dict_contains_camel_case_keys(self) -> None:
        payload = GenerationOptions(stopSequences=["</s>"]).toDict()
        assert payload["maxTokens"] == 128
        assert payload["stopSequences"] == ["</s>"]

    def test_training_result_dict(self) -> None:
        result = TrainingResult(steps=10, bestValLoss=1.5, tokensSeen=1000)
        payload = result.toDict()
        assert payload["steps"] == 10
        assert payload["tokensSeen"] == 1000
