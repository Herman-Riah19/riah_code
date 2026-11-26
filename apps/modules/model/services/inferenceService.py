# apps/modules/model/services/inferenceService.py
"""Inference service - lazy model loading, LRU cache and text generation."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

import torch

from apps.modules.shared.kernel.exceptions import (
    CheckpointNotFoundError,
    NoModelAvailableError,
    TokenizerNotFoundError,
    ValidationError,
)
from apps.modules.shared.kernel.lruCache import LRUCache
from apps.modules.tokenizer.models.tokenizerModel import BPETokenizer
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository

from ..ml.modelRunner import ModelRunner
from ..models.modelModel import Checkpoint, GenerationOptions, ModelConfig
from ..repositories.checkpointRepository import CheckpointRepository

ModelFactory = Callable[[ModelConfig], ModelRunner]
DEFAULT_CACHE_CAPACITY = 2


@dataclass(frozen=True)
class GenerationOutput:
    """Result of one non-streaming generation call."""

    prompt: str
    completion: str
    text: str
    generatedTokens: int
    checkpointId: str

    def toDict(self) -> dict[str, object]:
        """Serialize for API responses."""
        return {
            "prompt": self.prompt,
            "completion": self.completion,
            "text": self.text,
            "generatedTokens": self.generatedTokens,
            "checkpointId": self.checkpointId,
        }


class InferenceService:
    """Run generation on the best (or a chosen) checkpoint."""

    def __init__(
        self,
        tokenizerRepo: TokenizerRepository,
        checkpointRepo: CheckpointRepository,
        modelFactory: ModelFactory | None = None,
        modelCache: LRUCache[str, ModelRunner] | None = None,
        device: torch.device | None = None,
        cacheCapacity: int = DEFAULT_CACHE_CAPACITY,
    ) -> None:
        self._tokenizerRepo = tokenizerRepo
        self._checkpointRepo = checkpointRepo
        self._device = device
        self._modelFactory = modelFactory or self._defaultFactory
        self._cache = modelCache or LRUCache(capacity=cacheCapacity)

    # ----------------------------------------------------------------- models

    def _defaultFactory(self, config: ModelConfig) -> ModelRunner:
        """Build a runner on the configured device (CPU by default)."""
        return ModelRunner(config, device=self._device)

    def loadModel(self, checkpointId: str | None = None) -> ModelRunner:
        """Return a cached runner, loading and caching it on a miss."""
        if checkpointId is not None:
            cached = self._cache.get(checkpointId)
            if cached is not None:
                return cached

        checkpoint = self.resolveCheckpoint(checkpointId)
        cached = self._cache.get(checkpoint.id)
        if cached is not None:
            return cached

        runner = self._modelFactory(checkpoint.modelConfig)
        runner.loadCheckpoint(checkpoint)
        self._cache.put(checkpoint.id, runner)
        return runner

    def resolveCheckpoint(self, checkpointId: str | None) -> Checkpoint:
        """Return the requested checkpoint, or the best/latest one."""
        if checkpointId:
            checkpoint = self._checkpointRepo.findById(checkpointId)
            if checkpoint is None:
                raise CheckpointNotFoundError(
                    "Checkpoint introuvable",
                    details={"checkpointId": checkpointId},
                )
            return checkpoint

        checkpoint = self._checkpointRepo.findBest() or self._checkpointRepo.findLatest()
        if checkpoint is None:
            raise NoModelAvailableError("Aucun checkpoint disponible")
        return checkpoint

    def listModels(self, limit: int = 50) -> list[dict[str, object]]:
        """Return the model card of every indexed checkpoint."""
        return [
            self._modelInfo(checkpoint) for checkpoint in self._checkpointRepo.listAll(limit=limit)
        ]

    def getModelInfo(self, checkpointId: str) -> dict[str, object]:
        """Return the model card of one checkpoint."""
        return self._modelInfo(self.resolveCheckpoint(checkpointId))

    def unload(self, checkpointId: str) -> bool:
        """Drop one model from the cache."""
        return self._cache.pop(checkpointId) is not None

    def clearCache(self) -> None:
        """Drop every cached model."""
        self._cache.clear()

    @property
    def cacheSize(self) -> int:
        """Number of models currently cached."""
        return len(self._cache)

    # ------------------------------------------------------------- generation

    def generate(
        self,
        prompt: str,
        options: GenerationOptions,
        checkpointId: str | None = None,
    ) -> GenerationOutput:
        """Generate a completion and decode prompt + completion."""
        tokenizer, runner, checkpoint = self._prepare(prompt, checkpointId)
        promptIds = self._encodePrompt(tokenizer, prompt, runner.config.maxSeqLen)
        inputIds = torch.tensor([promptIds], dtype=torch.long)
        outputIds = runner.generate(inputIds, options)[0].tolist()
        generatedIds = outputIds[len(promptIds) :]
        return GenerationOutput(
            prompt=prompt,
            completion=tokenizer.decode(generatedIds),
            text=tokenizer.decode(outputIds),
            generatedTokens=len(generatedIds),
            checkpointId=checkpoint.id,
        )

    def streamGenerate(
        self,
        prompt: str,
        options: GenerationOptions,
        checkpointId: str | None = None,
    ) -> Iterator[str]:
        """Yield decoded text deltas as tokens are produced."""
        tokenizer, runner, _ = self._prepare(prompt, checkpointId)
        promptIds = self._encodePrompt(tokenizer, prompt, runner.config.maxSeqLen)
        inputIds = torch.tensor([promptIds], dtype=torch.long)
        for tokenId in runner.streamGenerate(inputIds, options):
            delta = tokenizer.decode([tokenId])
            if delta:
                yield delta

    # --------------------------------------------------------------- internals

    def _prepare(
        self,
        prompt: str,
        checkpointId: str | None,
    ) -> tuple[BPETokenizer, ModelRunner, Checkpoint]:
        """Validate the prompt and load the tokenizer plus the runner."""
        if not prompt or not prompt.strip():
            raise ValidationError("Le prompt ne peut pas etre vide")
        tokenizer = self._loadTokenizer()
        checkpoint = self.resolveCheckpoint(checkpointId)
        runner = self.loadModel(checkpoint.id)
        # The runner resolves stop sequences itself, so it needs the tokenizer.
        runner.setTokenizer(tokenizer)
        return tokenizer, runner, checkpoint

    def _loadTokenizer(self) -> BPETokenizer:
        """Load the project tokenizer, raising a domain error when missing."""
        try:
            tokenizer, _ = self._tokenizerRepo.load()
        except TokenizerNotFoundError:
            raise TokenizerNotFoundError(
                "Tokenizer introuvable: entrainez d'abord un tokenizer",
                details={"path": str(self._tokenizerRepo.tokenizerPath)},
            ) from None
        return tokenizer

    @staticmethod
    def _encodePrompt(
        tokenizer: BPETokenizer,
        prompt: str,
        maxSeqLen: int,
    ) -> list[int]:
        """Encode the prompt and keep its last `maxSeqLen` tokens."""
        tokenIds = tokenizer.encode(prompt, addSpecialTokens=False)
        if not tokenIds:
            raise ValidationError("Le prompt ne contient aucun token")
        return tokenIds[-maxSeqLen:]

    @staticmethod
    def _modelInfo(checkpoint: Checkpoint) -> dict[str, object]:
        """Build the model card returned by the models endpoints."""
        config = checkpoint.modelConfig
        return {
            "id": checkpoint.id,
            "modelName": checkpoint.modelName,
            "step": checkpoint.step,
            "epoch": checkpoint.epoch,
            "loss": checkpoint.loss,
            "valLoss": checkpoint.valLoss,
            "isBest": checkpoint.isBest,
            "createdAt": checkpoint.createdAt.isoformat(),
            "parameters": config.nParams,
            "architecture": {
                "nLayers": config.nLayers,
                "nHeads": config.nHeads,
                "nKvHeads": config.resolvedKvHeads,
                "dim": config.dim,
                "vocabSize": config.vocabSize,
                "maxSeqLen": config.maxSeqLen,
                "dtype": config.dtype,
            },
        }


__all__ = ["GenerationOutput", "InferenceService", "ModelFactory"]
