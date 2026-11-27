# apps/modules/model/ml/transformer.py
"""Decoder-only Transformer blocks and language model."""

from __future__ import annotations

from collections.abc import Iterator

import torch
from torch import nn
from torch.nn import functional as F

from ..models.modelConfig import ModelConfig
from .attention import KVCache, MultiHeadAttention
from .embedding import TokenEmbedding
from .feedForward import buildFeedForward
from .loss import crossEntropyLoss
from .normalization import buildNormalization
from .sampler import Sampler


class TransformerBlock(nn.Module):
    """Pre-norm block: attention + feed-forward with residual connections."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.attnNorm = buildNormalization(config)
        self.attention = MultiHeadAttention(config)
        self.ffnNorm = buildNormalization(config)
        self.feedForward = buildFeedForward(config)
        self.residDropout = nn.Dropout(config.residDropout)

    def forward(
        self,
        hiddenStates: torch.Tensor,
        pastKeyValue: KVCache | None = None,
        useCache: bool = False,
    ) -> tuple[torch.Tensor, KVCache | None]:
        """Apply attention then feed-forward, returning the updated cache."""
        attended, nextCache = self.attention(
            self.attnNorm(hiddenStates),
            pastKeyValue=pastKeyValue,
            useCache=useCache,
        )
        hiddenStates = hiddenStates + self.residDropout(attended)
        hiddenStates = hiddenStates + self.residDropout(
            self.feedForward(self.ffnNorm(hiddenStates))
        )
        return hiddenStates, nextCache


class TransformerLM(nn.Module):
    """Decoder-only Transformer language model with next-token prediction."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
        self.embedding = TokenEmbedding(config.vocabSize, config.dim)
        self.blocks = nn.ModuleList([TransformerBlock(config) for _ in range(config.nLayers)])
        self.finalNorm = buildNormalization(config)
        self.lmHead: nn.Linear | None = None
        if not config.tieEmbeddings:
            self.lmHead = nn.Linear(config.dim, config.vocabSize, bias=False)

        self.labelSmoothing = 0.0
        self.apply(self._initWeights)
        self._resetNormalizationParameters()

    def _initWeights(self, module: nn.Module) -> None:
        """Initialise projections/embeddings with a small normal distribution."""
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initStd)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initStd)

    def _resetNormalizationParameters(self) -> None:
        """Force every normalization layer to its neutral values."""
        for module in self.modules():
            weight = getattr(module, "weight", None)
            bias = getattr(module, "bias", None)
            if module.__class__.__name__ in {"RMSNorm", "LayerNormBlock"}:
                if weight is not None:
                    nn.init.ones_(weight)
                if bias is not None:
                    nn.init.zeros_(bias)

    def _projectLogits(self, hiddenStates: torch.Tensor) -> torch.Tensor:
        """Project hidden states to vocabulary logits (tied head when enabled)."""
        if self.lmHead is not None:
            return self.lmHead(hiddenStates)  # type: ignore[no-any-return]
        return F.linear(hiddenStates, self.embedding.embedding.weight)

    def forward(
        self,
        inputIds: torch.Tensor,
        targets: torch.Tensor | None = None,
        pastKeyValues: list[KVCache] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        """Return `(logits, loss)`; loss is None when no targets are provided."""
        hiddenStates = self.embedding(inputIds)
        for index, block in enumerate(self.blocks):
            pastKeyValue = pastKeyValues[index] if pastKeyValues is not None else None
            hiddenStates, _ = block(hiddenStates, pastKeyValue=pastKeyValue)
        hiddenStates = self.finalNorm(hiddenStates)
        logits = self._projectLogits(hiddenStates)
        loss = None
        if targets is not None:
            loss = crossEntropyLoss(logits, targets, self.labelSmoothing)
        return logits, loss

    def forwardCached(
        self,
        inputIds: torch.Tensor,
        pastKeyValues: list[KVCache] | None = None,
    ) -> tuple[torch.Tensor, list[KVCache]]:
        """Return `(logits, caches)` for incremental generation."""
        hiddenStates = self.embedding(inputIds)
        nextCaches: list[KVCache] = []
        for index, block in enumerate(self.blocks):
            pastKeyValue = pastKeyValues[index] if pastKeyValues is not None else None
            hiddenStates, cache = block(hiddenStates, pastKeyValue=pastKeyValue, useCache=True)
            if cache is None:  # pragma: no cover - defensive
                raise RuntimeError("attention block did not return a KV cache")
            nextCaches.append(cache)
        hiddenStates = self.finalNorm(hiddenStates)
        return self._projectLogits(hiddenStates), nextCaches

    @torch.inference_mode()
    def stream_generate(
        self,
        inputIds: torch.Tensor,
        maxTokens: int,
        sampler: Sampler,
    ) -> Iterator[int]:
        """Yield generated token ids one by one (KV-cached)."""
        if inputIds.dim() != 2 or inputIds.size(0) != 1:
            raise ValueError("generation expects a prompt of shape (1, seqLen)")
        if maxTokens <= 0:
            return

        device = next(self.parameters()).device
        tokens = inputIds.to(device)
        if tokens.size(1) > self.config.maxSeqLen:
            tokens = tokens[:, -self.config.maxSeqLen :]

        generatedTokens = tokens[0].tolist()
        logits, caches = self.forwardCached(tokens)

        for _ in range(maxTokens):
            nextToken = sampler.sample(logits[:, -1, :], generatedTokens)
            tokenId = int(nextToken.item())
            generatedTokens.append(tokenId)
            yield tokenId
            if sampler.isStopToken(tokenId):
                break
            if caches[0][0].shape[2] >= self.config.maxSeqLen:
                break
            logits, caches = self.forwardCached(nextToken, caches)

    def generate(
        self,
        inputIds: torch.Tensor,
        maxTokens: int,
        sampler: Sampler,
    ) -> torch.Tensor:
        """Return the prompt followed by the generated tokens."""
        generated = list(self.stream_generate(inputIds, maxTokens, sampler))
        if not generated:
            return inputIds
        device = inputIds.device
        extension = torch.tensor([generated], dtype=torch.long, device=device)
        return torch.cat((inputIds, extension), dim=1)

    def numParameters(self) -> int:
        """Count every trainable parameter of the model."""
        return sum(parameter.numel() for parameter in self.parameters())
