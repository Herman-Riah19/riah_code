# tests/unit/test_model/fakes.py
"""Shared fakes, builders and worker pools for the model unit tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
from tinyModel import tinyModelConfig

from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.models.modelModel import Checkpoint, ModelConfig
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.shared.kernel.exceptions import TokenizerNotFoundError

DEFAULT_EOS_TOKEN_ID = 63
LETTERS_ALPHABET_SIZE = 26
FAKE_TOKENIZER_PATH = Path("fake/tokenizer.json")


class FakeTokenizer:
    """Character tokenizer with a small, deterministic id space."""

    tokenizerPath = FAKE_TOKENIZER_PATH

    def __init__(self, encodeTo: int | None = None) -> None:
        # When `encodeTo` is set, every character maps to that single token id.
        self._encodeTo = encodeTo

    def encode(self, text: str, addSpecialTokens: bool = False) -> list[int]:
        """Encode text as `ord(char) % 64`, or as a fixed id when configured."""
        if self._encodeTo is not None:
            return [self._encodeTo] * len(text)
        return [ord(character) % 64 for character in text]

    def decode(self, tokenIds: list[int], skipSpecialTokens: bool = True) -> str:
        """Decode ids as lowercase letters, one character per id."""
        return "".join(chr(ord("a") + tokenId % LETTERS_ALPHABET_SIZE) for tokenId in tokenIds)


class SilentTokenizer(FakeTokenizer):
    """Tokenizer that never produces any token (simulates empty input)."""

    def encode(self, text: str, addSpecialTokens: bool = False) -> list[int]:
        """Always return an empty token list."""
        return []


class FakeTokenizerRepository:
    """Tokenizer repository stub returning an in-memory tokenizer."""

    tokenizerPath = FAKE_TOKENIZER_PATH

    def __init__(
        self,
        fail: bool = False,
        tokenizer: FakeTokenizer | None = None,
    ) -> None:
        self._fail = fail
        self._tokenizer = tokenizer if tokenizer is not None else FakeTokenizer()

    def exists(self) -> bool:
        """A tokenizer exists unless the stub is configured to fail."""
        return not self._fail

    def load(self) -> tuple[FakeTokenizer, None]:
        """Return the fake tokenizer, or raise the domain error."""
        if self._fail:
            raise TokenizerNotFoundError(
                "Tokenizer introuvable",
                details={"path": str(self.tokenizerPath)},
            )
        return self._tokenizer, None


class InlineWorkerPool:
    """Run submitted jobs immediately, in the calling thread."""

    def submit(self, task: Any, *args: Any) -> None:
        """Execute the task synchronously."""
        task(*args)


class DeferredWorkerPool:
    """Record submitted jobs without running them."""

    def __init__(self) -> None:
        self.tasks: list[tuple[Any, tuple[Any, ...]]] = []

    def submit(self, task: Any, *args: Any) -> None:
        """Store the task for a later, explicit execution."""
        self.tasks.append((task, args))


def cpuModelFactory(modelConfig: ModelConfig) -> ModelRunner:
    """Build a deterministic CPU runner."""
    return ModelRunner(modelConfig, device=torch.device("cpu"))


def makeCheckpoint(
    baseDir: Path,
    repository: CheckpointRepository,
    checkpointId: str,
    *,
    step: int = 5,
    isBest: bool = False,
    modelName: str = "tiny",
    eosTokenId: int = DEFAULT_EOS_TOKEN_ID,
) -> Checkpoint:
    """Persist a checkpoint whose zeroed logits always pick token 0."""
    config = tinyModelConfig(eosTokenId=eosTokenId)
    runner = ModelRunner(config, device=torch.device("cpu"))
    for parameter in runner.model.parameters():
        parameter.data.zero_()

    path = baseDir / f"{checkpointId}.pt"
    runner.saveCheckpoint(path, step=step)
    checkpoint = Checkpoint(
        id=checkpointId,
        path=path,
        step=step,
        epoch=0,
        loss=1.0,
        valLoss=0.9,
        modelConfig=config,
        createdAt=datetime.now(UTC),
        isBest=isBest,
        modelName=modelName,
    )
    repository.save(checkpoint)
    return checkpoint


__all__ = [
    "DEFAULT_EOS_TOKEN_ID",
    "DeferredWorkerPool",
    "FakeTokenizer",
    "FakeTokenizerRepository",
    "InlineWorkerPool",
    "SilentTokenizer",
    "cpuModelFactory",
    "makeCheckpoint",
]
