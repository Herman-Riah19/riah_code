# apps/modules/corpus/pipelines/bibleScraper.py
"""Bible scraper using the public bible-api.com chapter endpoint."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ...shared.kernel.exceptions import RiahAppError
from ..models.corpusModel import BibleScraperConfig, RawDocument, ScrapeResult
from ..repositories.corpusRepository import CorpusRepository
from .httpScraper import HttpScraper

BIBLE_API_URL = "https://bible-api.com/data/{translation}/{book}/{chapter}"
BIBLE_BATCH_SIZE = 100


class BibleScraper(HttpScraper):
    """Collect Bible chapters as raw documents, one verse or one chapter each."""

    def __init__(self, config: BibleScraperConfig | None = None) -> None:
        self._config = config or BibleScraperConfig()

    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        """Iterate translations, books and chapters then persist raw documents."""
        startedAt = time.monotonic()
        errors: list[str] = []
        scraped = 0
        saved = 0
        batch: list[RawDocument] = []

        for language in self._config.languages:
            for translation in self._config.translationsPerLang.get(language, []):
                for book in self._config.bookIds:
                    for chapter in range(self._config.chapterStart, self._config.chapterEnd + 1):
                        url = BIBLE_API_URL.format(
                            translation=translation,
                            book=book,
                            chapter=chapter,
                        )
                        try:
                            payload = self._fetchJson(url)
                        except RiahAppError as error:
                            errors.append(str(error))
                            continue
                        verseTexts = self._extractVerses(payload)
                        if not verseTexts:
                            continue
                        documents = verseTexts if self._config.versePerDocument else [" ".join(verseTexts)]
                        for text in documents:
                            scraped += 1
                            batch.append(
                                RawDocument.create(
                                    source=self._config.source,
                                    url=url,
                                    language=language,
                                    text=text,
                                    metadata={
                                        "translation": translation,
                                        "book": book,
                                        "chapter": chapter,
                                    },
                                )
                            )
                        if len(batch) >= BIBLE_BATCH_SIZE:
                            saved += corpusRepo.saveRaw(batch)
                            batch = []

        if batch:
            saved += corpusRepo.saveRaw(batch)
        return ScrapeResult(
            documentsScraped=scraped,
            documentsSaved=saved,
            errors=errors,
            durationSeconds=time.monotonic() - startedAt,
        )

    def _extractVerses(self, payload: dict[str, Any]) -> list[str]:
        verses = payload.get("verses", [])
        return [
            str(verse.get("text", "")).strip()
            for verse in verses
            if str(verse.get("text", "")).strip()
        ]
