# apps/modules/corpus/pipelines/baseScraper.py
"""Abstract contract implemented by every corpus source scraper."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models.corpusModel import ScrapeResult
from ..repositories.corpusRepository import CorpusRepository

__all__ = ["BaseScraper", "ScrapeResult"]


class BaseScraper(ABC):
    """Scrape one source and persist the produced raw documents."""

    @abstractmethod
    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        """Run the scraper and return a summary of the run."""
