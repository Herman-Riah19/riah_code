# apps/modules/tokenizer/services/tokenizerService.py
"""Tokenizer service - job lifecycle for BPE training and corpus encoding."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.kernel.exceptions import (
    ResourceNotFoundError,
    TokenizerNotFoundError,
    ValidationError,
)
from apps.modules.shared.kernel.job import Job, JobRepository, JobStatus, JobType
from apps.modules.shared.kernel.workerPool import WorkerPool

from ..models.tokenizerModel import BPETokenizer, TokenizerConfig, VocabInfo
from ..pipelines.corpusEncoder import CorpusEncoder
from ..pipelines.tokenizerTrainer import TokenizerTrainer
from ..repositories.tokenizerRepository import TokenizerRepository


class TokenizerService:
    """Expose tokenizer use cases to the HTTP layer."""

    def __init__(
        self,
        tokenizerRepo: TokenizerRepository,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
        workerPool: WorkerPool,
    ) -> None:
        self._tokenizerRepo = tokenizerRepo
        self._corpusRepo = corpusRepo
        self._jobRepo = jobRepo
        self._workerPool = workerPool

    def trainTokenizer(
        self,
        config: TokenizerConfig,
        corpusSampleSize: int,
        languages: list[str],
        userId: str,
    ) -> Job:
        """Create a pending training job, queue it and return it."""
        job = Job.create(
            jobType=JobType.TOKENIZER_TRAINING,
            config={
                **self._serializeConfig(config),
                "corpusSampleSize": corpusSampleSize,
                "languages": list(languages),
            },
            userId=userId,
        )
        self._jobRepo.save(job)
        self._workerPool.submit(
            self._runTokenizerTraining,
            job.id,
            config,
            corpusSampleSize,
            languages,
        )
        return job

    def encodeFullCorpus(
        self,
        tokenizerPath: str | None,
        shardSizeTokens: int,
        languages: list[str] | None,
        userId: str,
    ) -> Job:
        """Create a pending encoding job, queue it and return it."""
        resolvedPath = self.resolveTokenizerPath(tokenizerPath)
        if not resolvedPath.is_file():
            raise TokenizerNotFoundError(
                "Tokenizer introuvable",
                details={"path": str(resolvedPath)},
            )

        job = Job.create(
            jobType=JobType.CORPUS_ENCODING,
            config={
                "tokenizerPath": str(resolvedPath),
                "shardSizeTokens": shardSizeTokens,
                "languages": list(languages) if languages else None,
            },
            userId=userId,
        )
        self._jobRepo.save(job)
        self._workerPool.submit(
            self._runCorpusEncoding,
            job.id,
            resolvedPath,
            shardSizeTokens,
            languages,
        )
        return job

    def getJob(self, jobId: str, userId: str) -> Job:
        """Return one job owned by the user, or raise when unknown."""
        job = self._jobRepo.findById(jobId)
        if job is None or job.userId != userId:
            raise ResourceNotFoundError("Job introuvable", details={"jobId": jobId})
        return job

    def getInfo(self) -> VocabInfo:
        """Return metadata of the currently stored tokenizer."""
        _, vocabInfo = self._tokenizerRepo.load()
        return vocabInfo

    def previewText(self, text: str) -> dict[str, Any]:
        """Tokenize a sample text for the dashboard playground."""
        tokenizer, _ = self._tokenizerRepo.load()
        tokenIds = tokenizer.encode(text, addSpecialTokens=False)
        tokenCount = len(tokenIds)
        characterCount = len(text)
        return {
            "text": text,
            "tokenCount": tokenCount,
            "characterCount": characterCount,
            "compressionRatio": characterCount / tokenCount if tokenCount else 0.0,
            "tokens": [tokenizer.idToToken(tokenId) or "" for tokenId in tokenIds],
            "tokenIds": tokenIds,
            "decoded": tokenizer.decode(tokenIds),
        }

    def getVocab(self) -> list[dict[str, int | str]]:
        """Return every (token, id) pair of the stored vocabulary."""
        tokenizer, _ = self._tokenizerRepo.load()
        return tokenizer.getAllTokens()

    def resolveTokenizerPath(self, tokenizerPath: str | None) -> Path:
        """Resolve a tokenizer path and forbid escaping the tokenizer directory."""
        if tokenizerPath is None:
            return self._tokenizerRepo.tokenizerPath

        candidate = Path(tokenizerPath)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        allowedDir = self._tokenizerRepo.baseDir.resolve()
        if not resolved.is_relative_to(allowedDir):
            raise ValidationError(
                "Chemin tokenizer hors du repertoire autorise",
                details={"path": tokenizerPath},
            )
        return resolved

    def _runTokenizerTraining(
        self,
        jobId: str,
        config: TokenizerConfig,
        corpusSampleSize: int,
        languages: list[str],
    ) -> None:
        job = self._startJob(jobId)
        if job is None:
            return
        try:
            trainer = TokenizerTrainer(config)
            texts = (
                document.text
                for document in self._corpusRepo.sampleClean(
                    corpusSampleSize,
                    languages,
                )
            )
            vocabInfo = trainer.train(texts)
            self._tokenizerRepo.save(trainer.hfTokenizer, vocabInfo)
            job.progress = vocabInfo.toDict()
            job.status = JobStatus.COMPLETED
        except Exception as error:  # noqa: BLE001 - surface any failure to the job
            job.status = JobStatus.FAILED
            job.error = str(error)
        finally:
            job.finishedAt = datetime.now(UTC)
            self._jobRepo.save(job)

    def _runCorpusEncoding(
        self,
        jobId: str,
        tokenizerPath: Path,
        shardSizeTokens: int,
        languages: list[str] | None,
    ) -> None:
        job = self._startJob(jobId)
        if job is None:
            return
        try:
            tokenizer = BPETokenizer(tokenizerPath)
            encoder = CorpusEncoder(
                tokenizer=tokenizer,
                corpusRepo=self._corpusRepo,
                shardSizeTokens=shardSizeTokens,
            )
            stats = encoder.encodeCorpus(self._corpusRepo.loadClean(languages))
            job.progress = stats.toDict()
            job.status = JobStatus.COMPLETED
        except Exception as error:  # noqa: BLE001 - surface any failure to the job
            job.status = JobStatus.FAILED
            job.error = str(error)
        finally:
            job.finishedAt = datetime.now(UTC)
            self._jobRepo.save(job)

    def _startJob(self, jobId: str) -> Job | None:
        job = self._jobRepo.findById(jobId)
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.startedAt = datetime.now(UTC)
        self._jobRepo.save(job)
        return job

    @staticmethod
    def _serializeConfig(config: TokenizerConfig) -> dict[str, Any]:
        return {
            "vocabSize": config.vocabSize,
            "minFrequency": config.minFrequency,
            "specialTokens": list(config.specialTokens),
            "byteFallback": config.byteFallback,
            "addPrefixSpace": config.addPrefixSpace,
            "trimWhitespace": config.trimWhitespace,
            "showProgress": config.showProgress,
            "numThreads": config.numThreads,
        }
