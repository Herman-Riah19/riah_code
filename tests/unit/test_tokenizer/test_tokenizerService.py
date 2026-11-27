# tests/unit/test_tokenizer/test_tokenizerService.py
"""Tests for the tokenizer service - job lifecycle and path safety."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from tinyCorpus import TINY_CORPUS_TEXTS

from apps.modules.corpus.models.corpusModel import CleanDocument
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.kernel.exceptions import (
    ResourceNotFoundError,
    TokenizerNotFoundError,
    ValidationError,
)
from apps.modules.shared.kernel.job import Job, JobRepository, JobStatus, JobType
from apps.modules.tokenizer.models.tokenizerModel import TokenizerConfig
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository
from apps.modules.tokenizer.services.tokenizerService import TokenizerService


class InlineWorkerPool:
    """Run submitted jobs immediately, in the calling thread."""

    def submit(self, task, *args):
        task(*args)


def makeCleanDocument(documentId: str, text: str) -> CleanDocument:
    """Build a clean document for the corpus repository."""
    return CleanDocument(
        id=documentId,
        source="wikipedia",
        language="fr",
        text=text,
        qualityScore=0.9,
        tokenCount=len(text.split()),
        cleanedAt=datetime.now(UTC),
    )


class ServiceFixture:
    """Bundle the service and its repositories for tests."""

    def __init__(self, tmp_path: Path) -> None:
        self.tokenizerRepo = TokenizerRepository(tmp_path / "tokenizer")
        self.corpusRepo = CorpusRepository(tmp_path / "corpus")
        self.jobRepo = JobRepository()
        self.service = TokenizerService(
            tokenizerRepo=self.tokenizerRepo,
            corpusRepo=self.corpusRepo,
            jobRepo=self.jobRepo,
            workerPool=InlineWorkerPool(),
        )

    def seedCorpus(self, count: int = 5) -> None:
        documents = [
            makeCleanDocument(f"doc-{index}", text)
            for index, text in enumerate(TINY_CORPUS_TEXTS[:count])
        ]
        self.corpusRepo.saveClean(documents)


@pytest.fixture
def fixture(tmp_path: Path) -> ServiceFixture:
    return ServiceFixture(tmp_path)


class TestTokenizerTrainingJob:
    """Training job lifecycle."""

    def test_training_job_completes(self, fixture: ServiceFixture) -> None:
        fixture.seedCorpus()

        job = fixture.service.trainTokenizer(
            config=TokenizerConfig(
                vocabSize=300,
                minFrequency=1,
                showProgress=False,
                numThreads=2,
            ),
            corpusSampleSize=100,
            languages=["fr"],
            userId="user-1",
        )

        assert job.status == JobStatus.COMPLETED
        assert job.error is None
        assert job.finishedAt is not None
        assert job.progress["vocabSize"] > 0
        assert fixture.tokenizerRepo.exists() is True
        assert fixture.jobRepo.findById(job.id) is job

    def test_training_job_fails_on_empty_corpus(self, fixture: ServiceFixture) -> None:
        job = fixture.service.trainTokenizer(
            config=TokenizerConfig(vocabSize=300, showProgress=False),
            corpusSampleSize=100,
            languages=["fr"],
            userId="user-1",
        )

        assert job.status == JobStatus.FAILED
        assert job.error is not None
        assert "Corpus vide" in job.error
        assert fixture.tokenizerRepo.exists() is False

    def test_training_respects_language_filter(self, fixture: ServiceFixture) -> None:
        fixture.seedCorpus()

        job = fixture.service.trainTokenizer(
            config=TokenizerConfig(
                vocabSize=300,
                minFrequency=1,
                showProgress=False,
                numThreads=2,
            ),
            corpusSampleSize=100,
            languages=["en"],
            userId="user-1",
        )

        assert job.status == JobStatus.FAILED
        assert job.error is not None
        assert "Corpus vide" in job.error


class TestCorpusEncodingJob:
    """Encoding job lifecycle."""

    def test_encoding_job_completes(self, fixture: ServiceFixture) -> None:
        fixture.seedCorpus()
        fixture.service.trainTokenizer(
            config=TokenizerConfig(
                vocabSize=300,
                minFrequency=1,
                showProgress=False,
                numThreads=2,
            ),
            corpusSampleSize=100,
            languages=["fr"],
            userId="user-1",
        )

        job = fixture.service.encodeFullCorpus(
            tokenizerPath=None,
            shardSizeTokens=20,
            languages=None,
            userId="user-1",
        )

        assert job.status == JobStatus.COMPLETED
        assert job.error is None
        assert job.progress["totalDocuments"] == 5
        assert job.progress["shardCount"] >= 1
        assert len(fixture.corpusRepo.getShardsForTraining()) == job.progress["shardCount"]

    def test_encoding_without_tokenizer_fails(self, fixture: ServiceFixture) -> None:
        with pytest.raises(TokenizerNotFoundError):
            fixture.service.encodeFullCorpus(
                tokenizerPath=None,
                shardSizeTokens=20,
                languages=None,
                userId="user-1",
            )

    def test_encoding_rejects_path_outside_tokenizer_dir(
        self,
        fixture: ServiceFixture,
    ) -> None:
        with pytest.raises(ValidationError):
            fixture.service.encodeFullCorpus(
                tokenizerPath="../../etc/passwd",
                shardSizeTokens=20,
                languages=None,
                userId="user-1",
            )


class TestTokenizerPathResolution:
    """Path resolution must stay inside the tokenizer directory."""

    def test_none_returns_stored_tokenizer_path(self, fixture: ServiceFixture) -> None:
        assert fixture.service.resolveTokenizerPath(None) == (fixture.tokenizerRepo.tokenizerPath)

    def test_absolute_path_inside_directory_is_allowed(
        self,
        fixture: ServiceFixture,
    ) -> None:
        candidate = str(fixture.tokenizerRepo.tokenizerPath)

        assert fixture.service.resolveTokenizerPath(candidate) == (
            fixture.tokenizerRepo.tokenizerPath.resolve()
        )

    def test_relative_path_outside_directory_is_rejected(
        self,
        fixture: ServiceFixture,
    ) -> None:
        with pytest.raises(ValidationError):
            fixture.service.resolveTokenizerPath("../tokenizer.json")

    def test_absolute_path_outside_directory_is_rejected(
        self,
        fixture: ServiceFixture,
    ) -> None:
        with pytest.raises(ValidationError):
            fixture.service.resolveTokenizerPath("C:/Windows/system32/drivers/etc/hosts")


class TestGetJob:
    """Job lookup is scoped to its owner."""

    def test_unknown_job_raises(self, fixture: ServiceFixture) -> None:
        with pytest.raises(ResourceNotFoundError):
            fixture.service.getJob("unknown", "user-1")

    def test_job_of_another_user_raises(self, fixture: ServiceFixture) -> None:
        job = Job.create(
            jobType=JobType.TOKENIZER_TRAINING,
            config={},
            userId="user-2",
        )
        fixture.jobRepo.save(job)

        with pytest.raises(ResourceNotFoundError):
            fixture.service.getJob(job.id, "user-1")

    def test_owner_can_read_job(self, fixture: ServiceFixture) -> None:
        job = Job.create(
            jobType=JobType.TOKENIZER_TRAINING,
            config={},
            userId="user-1",
        )
        fixture.jobRepo.save(job)

        assert fixture.service.getJob(job.id, "user-1") is job


class TestPreview:
    """Tokenize sample text for the dashboard playground."""

    def test_preview_requires_tokenizer(self, fixture: ServiceFixture) -> None:
        with pytest.raises(TokenizerNotFoundError):
            fixture.service.previewText("Bonjour le monde.")

    def test_preview_returns_tokens(self, fixture: ServiceFixture) -> None:
        fixture.seedCorpus()
        fixture.service.trainTokenizer(
            config=TokenizerConfig(
                vocabSize=300,
                minFrequency=1,
                showProgress=False,
                numThreads=2,
            ),
            corpusSampleSize=100,
            languages=["fr"],
            userId="user-1",
        )
        text = "Le petit chat dort sur le tapis."

        preview = fixture.service.previewText(text)

        assert preview["characterCount"] == len(text)
        assert preview["tokenCount"] > 0
        assert len(preview["tokens"]) == preview["tokenCount"]
        assert len(preview["tokenIds"]) == preview["tokenCount"]
        assert preview["compressionRatio"] == len(text) / preview["tokenCount"]
        assert preview["decoded"].strip() == text
