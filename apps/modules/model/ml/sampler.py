# apps/modules/model/ml/sampler.py
"""Token sampling strategies (temperature, top-k, top-p, repetition penalty)."""

from __future__ import annotations

import torch
from torch.nn import functional as F


class Sampler:
    """Turn next-token logits into sampled token ids."""

    def __init__(
        self,
        temperature: float = 1.0,
        topK: int | None = None,
        topP: float = 1.0,
        repetitionPenalty: float = 1.0,
        stopTokenIds: list[int] | None = None,
        eosTokenId: int = 0,
        generator: torch.Generator | None = None,
    ) -> None:
        if temperature < 0:
            raise ValueError("temperature must be >= 0")
        if topK is not None and topK < 0:
            raise ValueError("topK must be >= 0")
        if not 0 < topP <= 1.0:
            raise ValueError("topP must be in ]0, 1]")
        if repetitionPenalty <= 0:
            raise ValueError("repetitionPenalty must be > 0")

        self.temperature = temperature
        self.topK = topK
        self.topP = topP
        self.repetitionPenalty = repetitionPenalty
        self.stopTokenIds = set(stopTokenIds or [])
        self.eosTokenId = eosTokenId
        self.generator = generator

    def sample(
        self,
        logits: torch.Tensor,
        generatedTokens: list[int] | None = None,
    ) -> torch.Tensor:
        """Sample one token per batch row from `(batch, vocab)` logits."""
        scores = logits.clone().float()

        if generatedTokens and self.repetitionPenalty != 1.0:
            tokenIds = torch.tensor(
                sorted(set(generatedTokens)), device=scores.device, dtype=torch.long
            )
            selected = scores.index_select(-1, tokenIds)
            # Standard CTRL penalty: shrink positive logits, grow negative ones.
            penalized = torch.where(
                selected > 0,
                selected / self.repetitionPenalty,
                selected * self.repetitionPenalty,
            )
            scatterIndex = tokenIds.unsqueeze(0).expand(scores.size(0), -1)
            scores.scatter_(-1, scatterIndex, penalized)

        if self.temperature <= 0:
            return torch.argmax(scores, dim=-1, keepdim=True)

        scores = scores / self.temperature

        if self.topK is not None and 0 < self.topK < scores.size(-1):
            threshold = torch.topk(scores, self.topK, dim=-1).values[..., -1:]
            scores = scores.masked_fill(scores < threshold, float("-inf"))

        if self.topP < 1.0:
            scores = self._applyTopP(scores)

        probabilities = F.softmax(scores, dim=-1)
        return torch.multinomial(
            probabilities,
            num_samples=1,
            generator=self.generator,
        )

    def _applyTopP(self, scores: torch.Tensor) -> torch.Tensor:
        """Keep the smallest nucleus whose cumulative probability exceeds topP."""
        sortedScores, sortedIndices = torch.sort(scores, descending=True, dim=-1)
        cumulative = F.softmax(sortedScores, dim=-1).cumsum(dim=-1)
        remove = cumulative > self.topP
        # Always keep the most likely token.
        remove[..., 1:] = remove[..., :-1].clone()
        remove[..., 0] = False
        filtered = sortedScores.masked_fill(remove, float("-inf"))
        return filtered.scatter(-1, sortedIndices, filtered)

    def isStopToken(self, tokenId: int) -> bool:
        """Return True when generation must stop on this token."""
        return tokenId == self.eosTokenId or tokenId in self.stopTokenIds
