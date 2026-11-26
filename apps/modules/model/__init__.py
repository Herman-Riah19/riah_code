# apps/modules/model/__init__.py
"""Model Module - Transformer architecture, training, and inference."""

from .controllers.inferenceController import InferenceContainer, inferenceBlueprint
from .controllers.trainingController import TrainingContainer, trainingBlueprint
from .ml.modelRunner import ModelRunner
from .ml.sampler import Sampler
from .ml.transformer import TransformerBlock, TransformerLM
from .models.modelModel import (
    MODEL_PRESETS,
    Checkpoint,
    GenerateRequest,
    GenerationOptions,
    ModelConfig,
    TrainingConfig,
    TrainingResult,
    TrainingResumeRequest,
    TrainingStartRequest,
)
from .pipelines.shardedDataset import ShardedTokenDataset
from .pipelines.trainingLoop import CancellationToken, Lion, TrainingLoop
from .repositories.checkpointRepository import CheckpointRepository
from .repositories.modelRepository import ModelRepository
from .services.inferenceService import GenerationOutput, InferenceService
from .services.trainingService import TrainingService

__all__ = [
    "MODEL_PRESETS",
    "CancellationToken",
    "Checkpoint",
    "CheckpointRepository",
    "GenerateRequest",
    "GenerationOptions",
    "GenerationOutput",
    "InferenceContainer",
    "InferenceService",
    "Lion",
    "ModelConfig",
    "ModelRepository",
    "ModelRunner",
    "Sampler",
    "ShardedTokenDataset",
    "TrainingConfig",
    "TrainingContainer",
    "TrainingLoop",
    "TrainingResult",
    "TrainingResumeRequest",
    "TrainingService",
    "TrainingStartRequest",
    "TransformerBlock",
    "TransformerLM",
    "inferenceBlueprint",
    "trainingBlueprint",
]
