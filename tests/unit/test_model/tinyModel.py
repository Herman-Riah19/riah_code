# tests/unit/test_model/tinyModel.py
"""Tiny model helpers shared by model unit tests (CPU, fast)."""

from __future__ import annotations

from typing import Any

from apps.modules.model.models.modelModel import (
    GenerationOptions,
    ModelConfig,
    TrainingConfig,
)

TINY_VOCAB_SIZE = 64


def tinyModelConfig(**overrides: Any) -> ModelConfig:
    """Return a small CPU-friendly model configuration."""
    defaults: dict[str, Any] = {
        "vocabSize": TINY_VOCAB_SIZE,
        "maxSeqLen": 32,
        "nLayers": 2,
        "nHeads": 2,
        "dim": 16,
        "dtype": "fp32",
        "eosTokenId": 0,
    }
    defaults.update(overrides)
    return ModelConfig(**defaults)


def tinyTrainingConfig(**overrides: Any) -> TrainingConfig:
    """Return a small training configuration using the tiny model."""
    defaults: dict[str, Any] = {
        "modelConfig": tinyModelConfig(),
        "batchSize": 2,
        "seqLen": 8,
        "maxSteps": 3,
        "evalInterval": 2,
        "checkpointInterval": 2,
        "logInterval": 1,
        "dtype": "fp32",
    }
    defaults.update(overrides)
    return TrainingConfig(**defaults)


def tinyGenerationOptions(**overrides: Any) -> GenerationOptions:
    """Return deterministic generation options for tests."""
    defaults: dict[str, Any] = {
        "maxTokens": 4,
        "temperature": 0.0,
        "topK": None,
        "topP": 1.0,
        "repetitionPenalty": 1.0,
    }
    defaults.update(overrides)
    return GenerationOptions(**defaults)
