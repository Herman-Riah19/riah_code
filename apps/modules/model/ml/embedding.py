# apps/modules/model/ml/embedding.py
"""Token embedding and rotary position encoding (RoPE)."""
from __future__ import annotations

import torch
from torch import nn


class TokenEmbedding(nn.Module):
    """Lookup table mapping token ids to hidden states."""

    def __init__(self, vocabSize: int, dim: int) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocabSize, dim)

    def forward(self, tokenIds: torch.Tensor) -> torch.Tensor:
        """Return the embedding of each token id."""
        return self.embedding(tokenIds)


class RotaryEmbedding(nn.Module):
    """Pre-computed cos/sin tables for rotary position embeddings."""

    def __init__(
        self,
        headDim: int,
        maxSeqLen: int,
        theta: float = 10_000.0,
        scalingFactor: float = 1.0,
    ) -> None:
        super().__init__()
        if headDim % 2 != 0:
            raise ValueError(f"headDim must be even for RoPE, got {headDim}")
        if scalingFactor <= 0:
            raise ValueError("scalingFactor must be strictly positive")

        self.headDim = headDim
        self.maxSeqLen = maxSeqLen
        self.scalingFactor = scalingFactor

        inverseFrequencies = 1.0 / (
            theta ** (torch.arange(0, headDim, 2, dtype=torch.float32) / headDim)
        )
        positions = torch.arange(maxSeqLen, dtype=torch.float32) / scalingFactor
        frequencies = torch.outer(positions, inverseFrequencies)
        # Duplicate so the table matches the full head dimension (rotate-half layout).
        embeddings = torch.cat((frequencies, frequencies), dim=-1)
        self.register_buffer("cosTable", embeddings.cos(), persistent=False)
        self.register_buffer("sinTable", embeddings.sin(), persistent=False)

    def forward(
        self,
        seqLen: int,
        offset: int = 0,
        device: torch.device | None = None,
        dtype: torch.dtype | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return `(cos, sin)` tables of shape `(seqLen, headDim)`."""
        end = offset + seqLen
        if end > self.maxSeqLen:
            raise ValueError(
                f"Sequence length {end} exceeds RoPE cache ({self.maxSeqLen})"
            )
        cos = self.cosTable[offset:end]
        sin = self.sinTable[offset:end]
        if device is not None or dtype is not None:
            cos = cos.to(device=device, dtype=dtype)
            sin = sin.to(device=device, dtype=dtype)
        return cos, sin


def rotateHalf(values: torch.Tensor) -> torch.Tensor:
    """Rotate the last dimension by swapping halves with sign flips."""
    half = values.shape[-1] // 2
    first = values[..., :half]
    second = values[..., half:]
    return torch.cat((-second, first), dim=-1)


def applyRotaryEmbedding(
    values: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> torch.Tensor:
    """Apply RoPE to `(batch, heads, seqLen, headDim)` tensors."""
    cos = cos.unsqueeze(0).unsqueeze(0)
    sin = sin.unsqueeze(0).unsqueeze(0)
    return (values * cos) + (rotateHalf(values) * sin)
