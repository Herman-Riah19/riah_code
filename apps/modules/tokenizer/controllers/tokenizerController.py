# apps/modules/tokenizer/controllers/tokenizerController.py
"""Tokenizer HTTP controller and lazy composition root."""
from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.config import settings
from apps.modules.shared.decorators.auth import requireAuth
from apps.modules.shared.decorators.validation import validateInput
from apps.modules.shared.kernel.job import JobRepository
from apps.modules.shared.kernel.workerPool import WorkerPool

from ..models.tokenizerModel import (
    CorpusEncodeRequest,
    TokenizerPreviewRequest,
    TokenizerTrainRequest,
)
from ..repositories.tokenizerRepository import TokenizerRepository
from ..services.tokenizerService import TokenizerService

DEFAULT_WORKER_COUNT = 2

tokenizerBlueprint = Blueprint("tokenizer", __name__, url_prefix="/api/tokenizer")


class TokenizerContainer:
    """Lazily build and reuse the tokenizer module dependencies."""

    _tokenizerRepository: TokenizerRepository | None = None
    _corpusRepository: CorpusRepository | None = None
    _jobRepository: JobRepository | None = None
    _workerPool: WorkerPool | None = None
    _service: TokenizerService | None = None

    @classmethod
    def getTokenizerRepository(cls) -> TokenizerRepository:
        if cls._tokenizerRepository is None:
            cls._tokenizerRepository = TokenizerRepository(settings.tokenizerDir)
        return cls._tokenizerRepository

    @classmethod
    def getCorpusRepository(cls) -> CorpusRepository:
        if cls._corpusRepository is None:
            cls._corpusRepository = CorpusRepository(settings.corpusDir)
        return cls._corpusRepository

    @classmethod
    def getJobRepository(cls) -> JobRepository:
        if cls._jobRepository is None:
            cls._jobRepository = JobRepository()
        return cls._jobRepository

    @classmethod
    def getWorkerPool(cls) -> WorkerPool:
        if cls._workerPool is None:
            cls._workerPool = WorkerPool(maxWorkers=DEFAULT_WORKER_COUNT)
        return cls._workerPool

    @classmethod
    def getService(cls) -> TokenizerService:
        if cls._service is None:
            cls._service = TokenizerService(
                tokenizerRepo=cls.getTokenizerRepository(),
                corpusRepo=cls.getCorpusRepository(),
                jobRepo=cls.getJobRepository(),
                workerPool=cls.getWorkerPool(),
            )
        return cls._service


@tokenizerBlueprint.route("/train", methods=["POST"])
@requireAuth
@validateInput(TokenizerTrainRequest)
def trainTokenizer(validated: TokenizerTrainRequest, user: Any) -> Any:
    """Start a BPE tokenizer training job."""
    job = TokenizerContainer.getService().trainTokenizer(
        config=validated.toConfig(),
        corpusSampleSize=validated.corpusSampleSize,
        languages=validated.languages,
        userId=user.id,
    )
    return jsonify(job.toDict()), 202


@tokenizerBlueprint.route("/encode", methods=["POST"])
@requireAuth
@validateInput(CorpusEncodeRequest)
def encodeCorpus(validated: CorpusEncodeRequest, user: Any) -> Any:
    """Start a full-corpus encoding job."""
    job = TokenizerContainer.getService().encodeFullCorpus(
        tokenizerPath=validated.tokenizerPath,
        shardSizeTokens=validated.shardSizeTokens,
        languages=validated.languages,
        userId=user.id,
    )
    return jsonify(job.toDict()), 202


@tokenizerBlueprint.route("/status/<jobId>", methods=["GET"])
@requireAuth
def getTokenizerJobStatus(user: Any, jobId: str) -> Any:
    """Return the current state of one tokenizer job."""
    job = TokenizerContainer.getService().getJob(jobId, user.id)
    return jsonify(job.toDict())


@tokenizerBlueprint.route("/info", methods=["GET"])
@requireAuth
def getTokenizerInfo(user: Any) -> Any:
    """Return metadata of the stored tokenizer, or 404 when missing."""
    repository = TokenizerContainer.getTokenizerRepository()
    if not repository.exists():
        return jsonify({"exists": False}), 404
    vocabInfo = TokenizerContainer.getService().getInfo()
    return jsonify({"exists": True, "vocabInfo": vocabInfo.toDict()})


@tokenizerBlueprint.route("/preview", methods=["POST"])
@requireAuth
@validateInput(TokenizerPreviewRequest)
def previewTokens(validated: TokenizerPreviewRequest, user: Any) -> Any:
    """Tokenize a sample text with the stored tokenizer."""
    return jsonify(TokenizerContainer.getService().previewText(validated.text))
