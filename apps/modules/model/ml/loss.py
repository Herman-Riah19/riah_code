# apps/modules/model/ml/loss.py
"""Language-modelling losses."""

from __future__ import annotations

import torch
from torch.nn import functional as F

IGNORE_INDEX = -100


def crossEntropyLoss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    labelSmoothing: float = 0.0,
    ignoreIndex: int = IGNORE_INDEX,
) -> torch.Tensor:
    """Next-token cross entropy over flattened `(batch * seq)` positions."""
    if logits.shape[:-1] != targets.shape:
        raise ValueError(
            "logits and targets must share their leading dimensions, got "
            f"{tuple(logits.shape[:-1])} and {tuple(targets.shape)}"
        )
    return F.cross_entropy(
        logits.reshape(-1, logits.size(-1)),
        targets.reshape(-1),
        label_smoothing=labelSmoothing,
        ignore_index=ignoreIndex,
    )


def perplexity(loss: torch.Tensor | float) -> float:
    """Exponentiate a cross-entropy loss."""
    value = float(loss)
    return float(torch.exp(torch.tensor(value)))
