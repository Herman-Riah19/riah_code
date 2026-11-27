# apps/modules/model/ml/feedForward.py
"""Feed-forward networks used inside the Transformer blocks."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from ..models.modelConfig import ModelConfig


class SwiGLU(nn.Module):
    """Gated linear unit with SiLU activation (LLaMA-style FFN)."""

    def __init__(
        self,
        dim: int,
        hiddenDim: int,
        dropout: float = 0.0,
        useBias: bool = False,
    ) -> None:
        super().__init__()
        self.gateProj = nn.Linear(dim, hiddenDim, bias=useBias)
        self.upProj = nn.Linear(dim, hiddenDim, bias=useBias)
        self.downProj = nn.Linear(hiddenDim, dim, bias=useBias)
        self.dropout = nn.Dropout(dropout)

    def forward(self, hiddenStates: torch.Tensor) -> torch.Tensor:
        """Apply the gated feed-forward transformation."""
        gate = F.silu(self.gateProj(hiddenStates))
        up = self.upProj(hiddenStates)
        return self.dropout(self.downProj(gate * up))  # type: ignore[no-any-return]


class GeGLU(nn.Module):
    """Gated linear unit with GELU activation."""

    def __init__(
        self,
        dim: int,
        hiddenDim: int,
        dropout: float = 0.0,
        useBias: bool = False,
    ) -> None:
        super().__init__()
        self.gateProj = nn.Linear(dim, hiddenDim, bias=useBias)
        self.upProj = nn.Linear(dim, hiddenDim, bias=useBias)
        self.downProj = nn.Linear(hiddenDim, dim, bias=useBias)
        self.dropout = nn.Dropout(dropout)

    def forward(self, hiddenStates: torch.Tensor) -> torch.Tensor:
        """Apply the gated feed-forward transformation."""
        gate = F.gelu(self.gateProj(hiddenStates))
        up = self.upProj(hiddenStates)
        return self.dropout(self.downProj(gate * up))  # type: ignore[no-any-return]


class GELUMlp(nn.Module):
    """Classic two-layer MLP with GELU activation."""

    def __init__(
        self,
        dim: int,
        hiddenDim: int,
        dropout: float = 0.0,
        useBias: bool = False,
    ) -> None:
        super().__init__()
        self.upProj = nn.Linear(dim, hiddenDim, bias=useBias)
        self.downProj = nn.Linear(hiddenDim, dim, bias=useBias)
        self.dropout = nn.Dropout(dropout)

    def forward(self, hiddenStates: torch.Tensor) -> torch.Tensor:
        """Apply the feed-forward transformation."""
        return self.dropout(self.downProj(F.gelu(self.upProj(hiddenStates))))  # type: ignore[no-any-return]


def buildFeedForward(config: ModelConfig) -> nn.Module:
    """Instantiate the feed-forward network selected by the config."""
    hiddenDim = config.resolvedDimFF
    if config.activation == "geglu":
        return GeGLU(config.dim, hiddenDim, config.ffnDropout, config.useBias)
    if config.activation == "gelu":
        return GELUMlp(config.dim, hiddenDim, config.ffnDropout, config.useBias)
    return SwiGLU(config.dim, hiddenDim, config.ffnDropout, config.useBias)
