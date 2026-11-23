# apps/modules/corpus/controllers/corpusController.py
"""Corpus HTTP controller and lazy composition root."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from flask import Blueprint, jsonify

from ...shared.config import settings
from ...shared.decorators.auth import requireAuth
from ...shared.decorators.validation import validateInput
from ...shared.kernel.exceptions import ResourceNotFoundError
from ...shared.kernel.job import JobRepository
from ...shared.kernel.workerPool import WorkerPool
from ..models.corpusModel import (
    BibleScraperConfig,
    PipelineConfig,
    PipelineStartRequest,
    ScrapeSourceDescription,
    WikiScraperConfig,
)
from ..pipelines.baseScraper import BaseScraper
from ..pipelines.bibleScraper import BibleScraper
from ..pipelines.deduplicator import Deduplicator
from ..pipelines.htmlCleaner import HtmlCleaner
from ..pipelines.markdownExporter import MarkdownExporter
from ..pipelines.pipelineOrchestrator import PipelineOrchestrator
from ..pipelines.qualityFilter import QualityFilter
from ..pipelines.shardWriter import ShardWriter
from ..pipelines.textNormalizer import TextNormalizer
from ..pipelines.wikiScraper import WikiScraper
from ..repositories.corpusRepository import CorpusRepository
from ..services.corpusService import CorpusService

DEFAULT_WORKER_COUNT = 4
WIKIPEDIA_SOURCE = "wikipedia"
BIBLE_SOURCE = "bible_gateway"
WIKIPEDIA_LANGUAGES = ("fr", "en", "es", "de")
BIBLE_TRANSLATIONS = {"fr": ["lsg"], "en": ["kjv"]}

SCRAPE_SOURCES = (
    ScrapeSourceDescription(
        id=WIKIPEDIA_SOURCE,
        label="Wikipedia",
        description="Articles encyclopediques via l'API publique de Wikipedia.",
        languages=list(WIKIPEDIA_LANGUAGES),
    ),
    ScrapeSourceDescription(
        id=BIBLE_SOURCE,
        label="Bible",
        description="Chapitres bibliques via l'API publique bible-api.com.",
        languages=list(BIBLE_TRANSLATIONS),
    ),
)

corpusBlueprint = Blueprint("corpus", __name__, url_prefix="/api/corpus")


class CorpusContainer:
    """Lazily build and reuse the corpus module dependencies."""

    _corpusRepository: CorpusRepository | None = None
    _jobRepository: JobRepository | None = None
    _workerPool: WorkerPool | None = None
    _service: CorpusService | None = None

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
    def buildScrapers(cls, config: PipelineConfig) -> list[BaseScraper]:
        """Instantiate only the scrapers requested by a pipeline configuration."""
        scrapers: list[BaseScraper] = []
        if WIKIPEDIA_SOURCE in config.sources:
            scrapers.append(
                WikiScraper(
                    WikiScraperConfig(
                        languages=list(config.languages),
                        maxArticlesPerLang=config.maxArticlesPerLang,
                        useDump=False,
                    )
                )
            )
        if BIBLE_SOURCE in config.sources:
            languages = [
                language for language in config.languages if language in BIBLE_TRANSLATIONS
            ]
            scrapers.append(
                BibleScraper(
                    BibleScraperConfig(
                        languages=languages or ["en"],
                        translationsPerLang={
                            language: BIBLE_TRANSLATIONS[language]
                            for language in BIBLE_TRANSLATIONS
                        },
                        versePerDocument=False,
                    )
                )
            )
        return scrapers

    @classmethod
    def buildOrchestrator(cls, config: PipelineConfig) -> PipelineOrchestrator:
        """Build a pipeline orchestrator preconfigured for one corpus run."""
        corpusRepo = cls.getCorpusRepository()
        return PipelineOrchestrator(
            scrapers=cls.buildScrapers(config),
            cleaner=HtmlCleaner(),
            normalizer=TextNormalizer(),
            qualityFilter=QualityFilter(),
            deduplicator=Deduplicator(),
            shardWriter=ShardWriter(),
            corpusRepo=corpusRepo,
            checkpointDir=settings.corpusDir / "checkpoints",
            markdownExporter=MarkdownExporter(),
            markdownDir=corpusRepo.getMarkdownDir(),
        )

    @classmethod
    def getService(cls) -> CorpusService:
        if cls._service is None:
            defaultConfig = PipelineConfig(outputDir=settings.corpusDir)
            cls._workerPool = WorkerPool(maxWorkers=DEFAULT_WORKER_COUNT)
            cls._service = CorpusService(
                orchestrator=cls.buildOrchestrator(defaultConfig),
                corpusRepo=cls.getCorpusRepository(),
                jobRepo=cls.getJobRepository(),
                workerPool=cls._workerPool,
                orchestratorFactory=cls.buildOrchestrator,
            )
        return cls._service


@corpusBlueprint.route("/pipeline/start", methods=["POST"])
@requireAuth
@validateInput(PipelineStartRequest)
def startPipeline(validated: PipelineStartRequest, user: Any) -> Any:
    """Start a corpus pipeline and return the created job."""
    jobId = CorpusContainer.getService().startPipeline(
        validated.toPipelineConfig(),
        userId=user.id,
    )
    job = CorpusContainer.getJobRepository().findById(jobId)
    return jsonify(job.toDict() if job else {"id": jobId}), 202


@corpusBlueprint.route("/pipeline/<jobId>/status", methods=["GET"])
@requireAuth
def getPipelineStatus(user: Any, jobId: str) -> Any:
    """Return the current state of one pipeline job."""
    job = CorpusContainer.getJobRepository().findById(jobId)
    if job is None or job.userId != user.id:
        raise ResourceNotFoundError("Job introuvable", details={"jobId": jobId})
    return jsonify(job.toDict())


@corpusBlueprint.route("/pipeline/<jobId>/resume", methods=["POST"])
@requireAuth
def resumePipeline(user: Any, jobId: str) -> Any:
    """Requeue a pipeline job from its last checkpoint."""
    job = CorpusContainer.getService().resumePipeline(jobId)
    return jsonify(job.toDict())


@corpusBlueprint.route("/stats", methods=["GET"])
@requireAuth
def getCorpusStats(user: Any) -> Any:
    """Return aggregated corpus statistics."""
    stats = CorpusContainer.getService().getStats()
    return jsonify(asdict(stats))


@corpusBlueprint.route("/datasets", methods=["GET"])
@requireAuth
def listCorpusDatasets(user: Any) -> Any:
    """List exported `.md` corpora grouped by source."""
    datasets = CorpusContainer.getCorpusRepository().listMarkdownCorpora()
    return jsonify({"datasets": [dataset.toDict() for dataset in datasets]})


@corpusBlueprint.route("/sources", methods=["GET"])
@requireAuth
def listScrapeSources(user: Any) -> Any:
    """List the scraping sources and languages available to the dashboard."""
    return jsonify({"sources": [asdict(source) for source in SCRAPE_SOURCES]})
