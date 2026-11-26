# apps/modules/corpus/__init__.py
"""Corpus Module - Data scraping, cleaning, and preparation."""

from .controllers.corpusController import CorpusContainer, corpusBlueprint
from .models.corpusModel import (
    BibleScraperConfig,
    CleanDocument,
    CorpusDatasetSummary,
    CorpusStats,
    DeduplicatorConfig,
    HtmlCleanerConfig,
    PipelineConfig,
    PipelineResult,
    PipelineStartRequest,
    QualityFilterConfig,
    RawDocument,
    ScrapeResult,
    ScrapeSourceDescription,
    ShardInfo,
    TextNormalizerConfig,
    WikiScraperConfig,
)
from .pipelines.baseScraper import BaseScraper
from .pipelines.bibleScraper import BibleScraper
from .pipelines.markdownExporter import MarkdownExporter
from .pipelines.pipelineOrchestrator import PipelineOrchestrator
from .pipelines.valtortaScraper import ValtortaScraper
from .repositories.corpusRepository import CorpusRepository
from .services.corpusService import CorpusService

__all__ = [
    "BibleScraperConfig",
    "CleanDocument",
    "CorpusDatasetSummary",
    "CorpusStats",
    "DeduplicatorConfig",
    "HtmlCleanerConfig",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStartRequest",
    "QualityFilterConfig",
    "RawDocument",
    "ScrapeResult",
    "ScrapeSourceDescription",
    "ShardInfo",
    "TextNormalizerConfig",
    "WikiScraperConfig",
    "BaseScraper",
    "BibleScraper",
    "ValtortaScraper",
    "MarkdownExporter",
    "PipelineOrchestrator",
    "CorpusRepository",
    "CorpusService",
    "CorpusContainer",
    "corpusBlueprint",
]
