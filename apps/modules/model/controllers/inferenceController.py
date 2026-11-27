# apps/modules/model/controllers/inferenceController.py
"""Inference HTTP controller and lazy composition root."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from apps.modules.shared.config import settings
from apps.modules.shared.decorators.auth import requireAuth
from apps.modules.shared.decorators.validation import validateInput
from apps.modules.shared.kernel.exceptions import ValidationError
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository

from ..models.generationModel import GenerateRequest
from ..repositories.checkpointRepository import CheckpointRepository
from ..services.inferenceService import InferenceService
from ..services.gpuExecutionCoordinator import gpuExecutionCoordinator

DEFAULT_CACHE_CAPACITY = 2

inferenceBlueprint = Blueprint("inference", __name__, url_prefix="/api/inference")


class InferenceContainer:
    """Lazily build and reuse the inference dependencies."""

    _checkpointRepository: CheckpointRepository | None = None
    _tokenizerRepository: TokenizerRepository | None = None
    _service: InferenceService | None = None

    @classmethod
    def getCheckpointRepository(cls) -> CheckpointRepository:
        if cls._checkpointRepository is None:
            cls._checkpointRepository = CheckpointRepository(settings.checkpointDir)
        return cls._checkpointRepository

    @classmethod
    def getTokenizerRepository(cls) -> TokenizerRepository:
        if cls._tokenizerRepository is None:
            cls._tokenizerRepository = TokenizerRepository(settings.tokenizerDir)
        return cls._tokenizerRepository

    @classmethod
    def getService(cls) -> InferenceService:
        if cls._service is None:
            cls._service = InferenceService(
                tokenizerRepo=cls.getTokenizerRepository(),
                checkpointRepo=cls.getCheckpointRepository(),
                gpuCoordinator=gpuExecutionCoordinator,
                cacheCapacity=DEFAULT_CACHE_CAPACITY,
            )
        return cls._service


@inferenceBlueprint.route("/generate", methods=["POST"])
@requireAuth
@validateInput(GenerateRequest)
def generate(validated: GenerateRequest, user: Any) -> Any:
    """Generate a completion for one prompt."""
    output = InferenceContainer.getService().generate(
        prompt=validated.prompt,
        options=validated.toOptions(),
        checkpointId=validated.checkpointId,
    )
    return jsonify(output.toDict())


@inferenceBlueprint.route("/models", methods=["GET"])
@requireAuth
def listModels(user: Any) -> Any:
    """List the checkpoints available for inference."""
    limit = _intArg("limit", default=50, minimum=1, maximum=200)
    return jsonify(InferenceContainer.getService().listModels(limit=limit))


@inferenceBlueprint.route("/models/<checkpointId>", methods=["GET"])
@requireAuth
def getModel(user: Any, checkpointId: str) -> Any:
    """Return the model card of one checkpoint."""
    return jsonify(InferenceContainer.getService().getModelInfo(checkpointId))


def _intArg(name: str, default: int, minimum: int, maximum: int | None = None) -> int:
    """Parse and bound an integer query parameter."""
    rawValue = request.args.get(name)
    if rawValue is None or rawValue == "":
        return default
    try:
        value = int(rawValue)
    except ValueError:
        raise ValidationError(
            f"Parametre {name} invalide",
            details={"value": rawValue},
        ) from None
    if value < minimum or (maximum is not None and value > maximum):
        raise ValidationError(
            f"Parametre {name} hors bornes",
            details={"value": value, "minimum": minimum, "maximum": maximum},
        )
    return value


__all__ = ["InferenceContainer", "inferenceBlueprint"]
