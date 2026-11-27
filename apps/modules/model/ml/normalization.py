# apps/modules/model/ml/normalization.py
"""Normalization layers used by the Transformer blocks."""

from __future__ import annotations

import torch
from torch import nn

from ..models.modelConfig import ModelConfig


class RMSNorm(nn.Module):
    """Root-mean-square normalization (computed in float32 for stability)."""

    def __init__(self, dim: int, eps: float = 1e-5) -> None:
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, hiddenStates: torch.Tensor) -> torch.Tensor:
        """Normalize the last dimension."""
        sourceDtype = hiddenStates.dtype
        values = hiddenStates.float()
        variance = values.pow(2).mean(dim=-1, keepdim=True)
        normalized = values * torch.rsqrt(variance + self.eps)
        return (normalized * self.weight.float()).to(sourceDtype)

    def extra_repr(self) -> str:
        """Show the dimension and epsilon in module summaries."""
        return f"dim={self.weight.numel()}, eps={self.eps}"


class LayerNormBlock(nn.Module):
    """LayerNorm wrapper kept alongside RMSNorm for config parity."""

    def __init__(self, dim: int, eps: float = 1e-5) -> None:
        super().__init__()
        self.norm = nn.LayerNorm(dim, eps=eps)

    def forward(self, hiddenStates: torch.Tensor) -> torch.Tensor:
        """Normalize the last dimension."""
        return self.norm(hiddenStates)  # type: ignore[no-any-return]


def buildNormalization(config: ModelConfig) -> nn.Module:
    """Instantiate the normalization layer selected by the config."""
    if config.normType == "layernorm":
        return LayerNormBlock(config.dim, config.normEps)
    return RMSNorm(config.dim, config.normEps)
