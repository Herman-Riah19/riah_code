# apps/modules/model/models/modelModel.py
"""Model domain models - architecture, training, checkpoints and generation."""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
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
            raise ValueError(
                f"dim ({self.dim}) must be divisible by nHeads ({self.nHeads})"
            )
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


@dataclass(frozen=True)
class TrainingConfig:
    """Everything needed to run or resume a training job."""

    modelConfig: ModelConfig
    trainShards: list[Path] = field(default_factory=list)
    valShards: list[Path] = field(default_factory=list)
    batchSize: int = 32
    microBatchSize: int | None = None
    seqLen: int = 2048
    numWorkers: int = 4

    optimizer: Literal["adamw", "adamw8bit", "lion"] = "adamw"
    lr: float = 3e-4
    minLr: float = 3e-5
    weightDecay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    eps: float = 1e-8
    gradClip: float = 1.0

    scheduler: Literal["cosine", "cosine_warmup", "constant", "wsd"] = "cosine_warmup"
    warmupSteps: int = 2000
    decaySteps: int = 100_000

    maxSteps: int = 100_000
    maxEpochs: int | None = None
    gradientAccumulationSteps: int = 1
    evalInterval: int = 1000
    evalSteps: int = 100
    logInterval: int = 10

    checkpointDir: Path = Path("checkpoints")
    checkpointInterval: int = 5000
    keepLastNCheckpoints: int = 3
    saveOptimizer: bool = True
    saveRng: bool = True

    dtype: Literal["fp32", "fp16", "bf16"] = "bf16"
    useGradScaler: bool = True
    compileModel: bool = True
    tensorboard: bool = False
    labelSmoothing: float = 0.0

    seed: int = 42

    @property
    def effectiveBatchSize(self) -> int:
        """Batch size actually seen by the optimizer."""
        return self.batchSize * self.gradientAccumulationSteps

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives."""
        return {
            "modelConfig": self.modelConfig.toDict(),
            "trainShards": [str(path) for path in self.trainShards],
            "valShards": [str(path) for path in self.valShards],
            "batchSize": self.batchSize,
            "microBatchSize": self.microBatchSize,
            "seqLen": self.seqLen,
            "numWorkers": self.numWorkers,
            "optimizer": self.optimizer,
            "lr": self.lr,
            "minLr": self.minLr,
            "weightDecay": self.weightDecay,
            "beta1": self.beta1,
            "beta2": self.beta2,
            "eps": self.eps,
            "gradClip": self.gradClip,
            "scheduler": self.scheduler,
            "warmupSteps": self.warmupSteps,
            "decaySteps": self.decaySteps,
            "maxSteps": self.maxSteps,
            "maxEpochs": self.maxEpochs,
            "gradientAccumulationSteps": self.gradientAccumulationSteps,
            "evalInterval": self.evalInterval,
            "evalSteps": self.evalSteps,
            "logInterval": self.logInterval,
            "checkpointDir": str(self.checkpointDir),
            "checkpointInterval": self.checkpointInterval,
            "keepLastNCheckpoints": self.keepLastNCheckpoints,
            "saveOptimizer": self.saveOptimizer,
            "saveRng": self.saveRng,
            "dtype": self.dtype,
            "useGradScaler": self.useGradScaler,
            "compileModel": self.compileModel,
            "tensorboard": self.tensorboard,
            "labelSmoothing": self.labelSmoothing,
            "seed": self.seed,
        }

    @classmethod
    def fromDict(cls, payload: dict[str, Any]) -> TrainingConfig:
        """Rebuild a training config from a serialized payload."""
        data = dict(payload)
        data["modelConfig"] = ModelConfig.fromDict(data["modelConfig"])
        data["trainShards"] = [Path(path) for path in data.get("trainShards", [])]
        data["valShards"] = [Path(path) for path in data.get("valShards", [])]
        data["checkpointDir"] = Path(data.get("checkpointDir", "checkpoints"))
        known = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})


@dataclass(frozen=True)
class Checkpoint:
    """A persisted training snapshot plus its index metadata."""

    id: str
    path: Path
    step: int
    epoch: int
    loss: float
    modelConfig: ModelConfig
    createdAt: datetime
    valLoss: float | None = None
    trainingConfig: TrainingConfig | None = None
    isBest: bool = False
    modelName: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives."""
        return {
            "id": self.id,
            "path": str(self.path),
            "step": self.step,
            "epoch": self.epoch,
            "loss": self.loss,
            "valLoss": self.valLoss,
            "modelConfig": self.modelConfig.toDict(),
            "trainingConfig": (
                self.trainingConfig.toDict() if self.trainingConfig else None
            ),
            "createdAt": self.createdAt.isoformat(),
            "isBest": self.isBest,
            "modelName": self.modelName,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def fromDict(cls, payload: dict[str, Any]) -> Checkpoint:
        """Rebuild a checkpoint from a serialized payload."""
        return cls(
            id=payload["id"],
            path=Path(payload["path"]),
            step=int(payload["step"]),
            epoch=int(payload["epoch"]),
            loss=float(payload["loss"]),
            valLoss=float(payload["valLoss"]) if payload.get("valLoss") is not None else None,
            modelConfig=ModelConfig.fromDict(payload["modelConfig"]),
            trainingConfig=(
                TrainingConfig.fromDict(payload["trainingConfig"])
                if payload.get("trainingConfig")
                else None
            ),
            createdAt=datetime.fromisoformat(payload["createdAt"]),
            isBest=bool(payload.get("isBest", False)),
            modelName=payload.get("modelName"),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(frozen=True)
class GenerationOptions:
    """Sampling parameters for text generation."""

    maxTokens: int = 128
    temperature: float = 0.7
    topK: int | None = 50
    topP: float = 0.9
    repetitionPenalty: float = 1.1
    stopSequences: list[str] = field(default_factory=list)
    seed: int | None = None

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives."""
        return {
            "maxTokens": self.maxTokens,
            "temperature": self.temperature,
            "topK": self.topK,
            "topP": self.topP,
            "repetitionPenalty": self.repetitionPenalty,
            "stopSequences": list(self.stopSequences),
            "seed": self.seed,
        }


@dataclass(frozen=True)
class TrainingResult:
    """Outcome of a completed training run."""

    steps: int
    bestValLoss: float
    tokensSeen: int
    elapsedSeconds: float = 0.0
    finalLoss: float | None = None

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives."""
        return {
            "steps": self.steps,
            "bestValLoss": self.bestValLoss,
            "tokensSeen": self.tokensSeen,
            "elapsedSeconds": self.elapsedSeconds,
            "finalLoss": self.finalLoss,
        }
