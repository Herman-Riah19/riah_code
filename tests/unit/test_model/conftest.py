# tests/unit/test_model/conftest.py
"""Shared fixtures for model unit tests."""

from __future__ import annotations

import pytest
import torch

from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.ml.transformer import TransformerLM
from apps.modules.model.models.modelModel import ModelConfig

from tinyModel import tinyModelConfig


@pytest.fixture
def tinyConfig() -> ModelConfig:
    """Small CPU configuration for a single test."""
    return tinyModelConfig()


@pytest.fixture
def tinyModel(tinyConfig: ModelConfig) -> TransformerLM:
    """Fresh tiny TransformerLM in eval mode."""
    torch.manual_seed(1234)
    model = TransformerLM(tinyConfig)
    model.eval()
    return model


@pytest.fixture
def tinyRunner(tinyConfig: ModelConfig) -> ModelRunner:
    """Fresh tiny ModelRunner on CPU."""
    torch.manual_seed(1234)
    return ModelRunner(tinyConfig, device=torch.device("cpu"))
