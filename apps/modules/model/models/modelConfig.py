"""Transformer architecture configuration and built-in presets."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Literal


@dataclass(frozen=True)
class ModelConfig:
    """Immutable description of a decoder-only Transformer."""

    # Architecture
    vocabSize: int = 32_000
    maxSeqLen: int = 2048
    nLayers: int = 12
    nHeads: int = 12
    nKvHeads: int | None = None  # Grouped-query attention when < nHeads
    dim: int = 768
    dimFF: int | None = None

    # Normalization
    normType: Literal["rmsnorm", "layernorm"] = "rmsnorm"
    normEps: float = 1e-5

    # Attention
    attnImpl: Literal["eager", "flash", "sdpa"] = "sdpa"
    attnDropout: float = 0.0
    residDropout: float = 0.0
    useBias: bool = False
    useRoPE: bool = True
    ropeTheta: float = 10_000.0
    ropeScaling: dict[str, float] | None = None

    # Feed-forward
    activation: Literal["gelu", "swiglu", "geglu"] = "swiglu"
    ffnDropout: float = 0.0

    # Embedding
    tieEmbeddings: bool = True
    initStd: float = 0.02

    # Precision / compilation. `None` disables `torch.compile` (safer on CPU).
    dtype: Literal["fp32", "fp16", "bf16"] = "bf16"
    compileMode: Literal["default", "reduce-overhead", "max-autotune"] | None = None

    # Special tokens
    eosTokenId: int = 0
    bosTokenId: int | None = None
    padTokenId: int = 1

    @property
    def nParams(self) -> int:
        """Approximate parameter count (embedding + layers + head)."""
        embParams = self.vocabSize * self.dim
        attnParamsPerLayer = 4 * self.dim * self.dim
        ffnParamsPerLayer = 2 * self.dim * (self.dimFF or 4 * self.dim)
        layerParams = self.nLayers * (attnParamsPerLayer + ffnParamsPerLayer + 2 * self.dim)
        outParams = 0 if self.tieEmbeddings else self.vocabSize * self.dim
        return embParams + layerParams + outParams

    @property
    def headDim(self) -> int:
        """Dimension of a single attention head."""
        if self.dim % self.nHeads != 0:
            raise ValueError(f"dim ({self.dim}) must be divisible by nHeads ({self.nHeads})")
        return self.dim // self.nHeads

    @property
    def resolvedDimFF(self) -> int:
        """Feed-forward hidden size, defaulting to 4 x dim."""
        return self.dimFF or 4 * self.dim

    @property
    def resolvedKvHeads(self) -> int:
        """Number of key/value heads, defaulting to full multi-head."""
        return self.nKvHeads or self.nHeads

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives (JSON/SQLite friendly)."""
        payload = {f.name: getattr(self, f.name) for f in fields(self)}
        payload["ropeScaling"] = dict(self.ropeScaling) if self.ropeScaling else None
        return payload

    @classmethod
    def fromDict(cls, payload: dict[str, Any]) -> ModelConfig:
        """Rebuild a config, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in payload.items() if key in known})


MODEL_PRESETS: dict[str, ModelConfig] = {
    "tiny": ModelConfig(
        vocabSize=512,
        maxSeqLen=128,
        nLayers=2,
        nHeads=4,
        dim=64,
        dtype="fp32",
    ),
    "125M": ModelConfig(nLayers=12, nHeads=12, dim=768),
    "350M": ModelConfig(nLayers=24, nHeads=16, dim=1024),
    "760M": ModelConfig(nLayers=24, nHeads=16, dim=1536),
    "1.3B": ModelConfig(nLayers=24, nHeads=32, dim=2048),
}

__all__ = ["MODEL_PRESETS", "ModelConfig"]
