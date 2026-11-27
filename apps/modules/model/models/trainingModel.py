"""Training configuration, jobs and request models."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from apps.modules.shared.kernel.exceptions import ValidationError

from .modelConfig import MODEL_PRESETS, ModelConfig


@dataclass(frozen=True)
class TrainingConfig:
    """Everything needed to run or resume a training job."""

    modelConfig: ModelConfig
    trainShards: list[Path] = field(default_factory=list)
    valShards: list[Path] = field(default_factory=list)
    modelName: str = "default"
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
        return (self.microBatchSize or self.batchSize) * self.gradientAccumulationSteps

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives."""
        return {
            "modelConfig": self.modelConfig.toDict(),
            "trainShards": [str(path) for path in self.trainShards],
            "valShards": [str(path) for path in self.valShards],
            "modelName": self.modelName,
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
            "trainingConfig": (self.trainingConfig.toDict() if self.trainingConfig else None),
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


class TrainingStartRequest(BaseModel):
    """HTTP payload used to launch a training run."""

    preset: str = "125M"
    modelConfig: dict[str, Any] | None = None
    modelName: str = Field(
        default="default",
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    trainShards: list[str] | None = None
    valShards: list[str] | None = None

    batchSize: int = Field(default=8, ge=1, le=4096)
    microBatchSize: int | None = Field(default=None, ge=1, le=4096)
    seqLen: int = Field(default=512, ge=8, le=8192)
    numWorkers: int = Field(default=0, ge=0, le=32)

    optimizer: Literal["adamw", "adamw8bit", "lion"] = "adamw"
    lr: float = Field(default=3e-4, gt=0)
    minLr: float = Field(default=3e-5, ge=0)
    weightDecay: float = Field(default=0.1, ge=0)
    beta1: float = Field(default=0.9, ge=0, lt=1)
    beta2: float = Field(default=0.95, ge=0, lt=1)
    eps: float = Field(default=1e-8, gt=0)
    gradClip: float = Field(default=1.0, ge=0)

    scheduler: Literal["cosine", "cosine_warmup", "constant", "wsd"] = "cosine_warmup"
    warmupSteps: int = Field(default=2000, ge=0)
    decaySteps: int = Field(default=100_000, ge=1)

    maxSteps: int = Field(default=100_000, ge=1)
    maxEpochs: int | None = Field(default=None, ge=1)
    gradientAccumulationSteps: int = Field(default=1, ge=1)
    evalInterval: int = Field(default=1000, ge=0)
    evalSteps: int = Field(default=100, ge=1)
    logInterval: int = Field(default=10, ge=0)

    checkpointInterval: int = Field(default=5000, ge=0)
    keepLastNCheckpoints: int = Field(default=3, ge=1)
    saveOptimizer: bool = True
    saveRng: bool = True

    dtype: Literal["fp32", "fp16", "bf16"] = "bf16"
    useGradScaler: bool = True
    compileModel: bool = False
    tensorboard: bool = False
    labelSmoothing: float = Field(default=0.0, ge=0.0, lt=1.0)
    seed: int = Field(default=42, ge=0)

    @field_validator("preset")
    @classmethod
    def _validatePreset(cls, value: str) -> str:
        """Reject unknown architecture presets early."""
        if value not in MODEL_PRESETS:
            raise ValueError(f"preset inconnu: {value} (disponibles: {sorted(MODEL_PRESETS)})")
        return value

    def toModelConfig(self) -> ModelConfig:
        """Merge the preset with the optional architecture overrides."""
        payload = MODEL_PRESETS[self.preset].toDict()
        if self.modelConfig:
            payload.update(self.modelConfig)
        config = ModelConfig.fromDict(payload)
        try:
            _ = config.headDim
        except ValueError as error:
            raise ValidationError(
                "Configuration de modele invalide",
                details={"reason": str(error)},
            ) from error
        return config

    def toConfig(
        self,
        checkpointDir: Path,
        shardDir: Path | None = None,
    ) -> TrainingConfig:
        """Convert the validated request into a domain configuration."""
        modelConfig = self.toModelConfig()
        if self.seqLen > modelConfig.maxSeqLen:
            raise ValidationError(
                "seqLen depasse la fenetre de contexte du modele",
                details={"seqLen": self.seqLen, "maxSeqLen": modelConfig.maxSeqLen},
            )
        return TrainingConfig(
            modelConfig=modelConfig,
            trainShards=self._resolveShards(self.trainShards, shardDir),
            valShards=self._resolveShards(self.valShards, shardDir),
            modelName=self.modelName,
            batchSize=self.batchSize,
            microBatchSize=self.microBatchSize,
            seqLen=self.seqLen,
            numWorkers=self.numWorkers,
            optimizer=self.optimizer,
            lr=self.lr,
            minLr=self.minLr,
            weightDecay=self.weightDecay,
            beta1=self.beta1,
            beta2=self.beta2,
            eps=self.eps,
            gradClip=self.gradClip,
            scheduler=self.scheduler,
            warmupSteps=self.warmupSteps,
            decaySteps=self.decaySteps,
            maxSteps=self.maxSteps,
            maxEpochs=self.maxEpochs,
            gradientAccumulationSteps=self.gradientAccumulationSteps,
            evalInterval=self.evalInterval,
            evalSteps=self.evalSteps,
            logInterval=self.logInterval,
            checkpointDir=Path(checkpointDir),
            checkpointInterval=self.checkpointInterval,
            keepLastNCheckpoints=self.keepLastNCheckpoints,
            saveOptimizer=self.saveOptimizer,
            saveRng=self.saveRng,
            dtype=self.dtype,
            useGradScaler=self.useGradScaler,
            compileModel=self.compileModel,
            tensorboard=self.tensorboard,
            labelSmoothing=self.labelSmoothing,
            seed=self.seed,
        )

    @staticmethod
    def _resolveShards(
        explicit: list[str] | None,
        shardDir: Path | None,
    ) -> list[Path]:
        """Resolve explicit shard files, or fall back to the corpus directory."""
        if not explicit:
            if shardDir is None:
                return []
            return sorted(shardDir.glob("shard_*.bin"))

        allowedDir = shardDir.resolve() if shardDir is not None else None
        resolvedPaths: list[Path] = []
        for rawPath in explicit:
            candidate = Path(rawPath)
            if not candidate.is_absolute():
                candidate = Path.cwd() / candidate
            resolved = candidate.resolve()
            if not resolved.is_file():
                raise ValidationError(
                    "Shard introuvable",
                    details={"path": str(resolved)},
                )
            if allowedDir is not None and not resolved.is_relative_to(allowedDir):
                raise ValidationError(
                    "Shard hors du repertoire corpus autorise",
                    details={"path": str(resolved)},
                )
            resolvedPaths.append(resolved)
        return resolvedPaths


class TrainingResumeRequest(BaseModel):
    """HTTP payload used to resume a training job."""

    checkpointId: str | None = None
    maxSteps: int | None = Field(default=None, ge=1)
    lr: float | None = Field(default=None, gt=0)

    def applyTo(self, config: TrainingConfig) -> TrainingConfig:
        """Return the config with the optional overrides applied."""
        overrides: dict[str, Any] = {}
        if self.maxSteps is not None:
            overrides["maxSteps"] = self.maxSteps
        if self.lr is not None:
            overrides["lr"] = self.lr
        return replace(config, **overrides) if overrides else config


__all__ = [
    "Checkpoint",
    "TrainingConfig",
    "TrainingResult",
    "TrainingResumeRequest",
    "TrainingStartRequest",
]
