# apps/modules/corpus/pipelines/bibleScraper.py
"""Bible scraper - collects public domain Bible texts for training corpora.

Bible chapters are downloaded from the public-domain datasets maintained by
the ``scrollmapper/bible_databases`` project on GitHub. Each chapter becomes
one raw document and is later exported as a standalone markdown file.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from ..models.corpusModel import BibleScraperConfig, RawDocument, ScrapeResult
from ..repositories.corpusRepository import CorpusRepository
from .httpScraper import HttpScraper

BIBLE_JSON_BASE_URL = (
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json"
)
BIBLE_SAVE_BATCH_SIZE = 100


@dataclass(frozen=True)
class TranslationSource:
    """Location and encoding of one public-domain Bible translation."""

    fileName: str
    label: str
    encoding: str


TRANSLATION_CATALOG: dict[str, TranslationSource] = {
    "crampon": TranslationSource(
        fileName="FreCrampon.json",
        label="Augustin Crampon 1923",
        encoding="latin-1",
    ),
    "jnd": TranslationSource(
        fileName="FreJND.json",
        label="J. N. Darby",
        encoding="latin-1",
    ),
    "kjv": TranslationSource(
        fileName="KJV.json",
        label="King James Version",
        encoding="utf-8",
    ),
}


class BibleScraper(HttpScraper):
    """Collect complete public-domain Bibles, one document per chapter."""

    def __init__(self, config: BibleScraperConfig | None = None) -> None:
        self._config = config or BibleScraperConfig()

    def scrape(self, corpusRepo: CorpusRepository) -> ScrapeResult:
        """Download the requested translations and persist their chapters."""
        startedAt = time.monotonic()
        errors: list[str] = []
        scraped = 0
        saved = 0

        for language in self._config.languages:
            translationId = self._config.translationsPerLang.get(language)
            if translationId is None:
                errors.append(f"{language}: aucune traduction configuree")
                continue
            translation = TRANSLATION_CATALOG.get(translationId)
            if translation is None:
                errors.append(
                    f"{language}: traduction inconnue '{translationId}' "
                    f"(disponibles: {', '.join(sorted(TRANSLATION_CATALOG))})"
                )
                continue

            try:
                documents = self._downloadTranslation(language, translation)
            except Exception as error:  # noqa: BLE001 - surface any source failure
                errors.append(f"{language}/{translation.label}: {error}")
                continue

            scraped += len(documents)
            saved += self._saveInBatches(documents, corpusRepo)

        return ScrapeResult(
            documentsScraped=scraped,
            documentsSaved=saved,
            errors=errors,
            durationSeconds=time.monotonic() - startedAt,
        )

    def _downloadTranslation(
        self,
        language: str,
        translation: TranslationSource,
    ) -> list[RawDocument]:
        """Fetch one translation and convert every chapter into a document."""
        url = f"{BIBLE_JSON_BASE_URL}/{translation.fileName}"
        payload = self._fetchText(url, (translation.encoding, "utf-8"))
        data: dict[str, Any] = self._decodeJson(payload, url)
        return self._parseTranslation(data, language, translation, url)

    def _parseTranslation(
        self,
        data: dict[str, Any],
        language: str,
        translation: TranslationSource,
        url: str,
    ) -> list[RawDocument]:
        """Build one raw document per Bible chapter."""
        documents: list[RawDocument] = []
        for book in data.get("books", []):
            bookName = str(book.get("name", "Bible"))
            for chapter in book.get("chapters", []):
                chapterNumber = int(chapter.get("chapter", 0))
                verseTexts = [
                    str(verse.get("text", "")).strip() for verse in chapter.get("verses", [])
                ]
                content = " ".join(text for text in verseTexts if text)
                if len(content) < self._config.minArticleLength:
                    continue
                documents.append(
                    RawDocument.create(
                        source=self._config.source,
                        url=f"{url}#{bookName}/{chapterNumber}",
                        language=language,
                        text=content,
                        metadata={
                            "book": bookName,
                            "chapter": chapterNumber,
                            "translation": translation.label,
                            "source_type": "bible_public_domain",
                        },
                    )
                )
        return documents

    @staticmethod
    def _decodeJson(payload: str, url: str) -> dict[str, Any]:
        """Decode a JSON payload, reporting the offending URL on failure."""
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as error:
            raise ValueError(f"Reponse JSON invalide pour {url}: {error}") from error
        if not isinstance(decoded, dict):
            raise TypeError(f"Structure inattendue pour {url}")
        return decoded

    @staticmethod
    def _saveInBatches(
        documents: list[RawDocument],
        corpusRepo: CorpusRepository,
    ) -> int:
        """Persist documents in bounded batches to keep memory flat."""
        saved = 0
        for start in range(0, len(documents), BIBLE_SAVE_BATCH_SIZE):
            batch = documents[start : start + BIBLE_SAVE_BATCH_SIZE]
            saved += corpusRepo.saveRaw(batch)
        return saved
