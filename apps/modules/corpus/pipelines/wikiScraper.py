# apps/modules/corpus/pipelines/wikiScraper.py
"""Wikipedia scraper: REST API extraction or Wikimedia XML dump parsing."""
from __future__ import annotations

import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from ...shared.kernel.exceptions import RiahAppError, ValidationError
from ..models.corpusModel import RawDocument, ScrapeResult, WikiScraperConfig
from ..repositories.corpusRepository import CorpusRepository
from .httpScraper import HttpScraper

WIKI_API_URL = "https://{language}.wikipedia.org/w/api.php"
WIKI_BATCH_SIZE = 100
API_PAGE_LIMIT = 20


class WikiScraper(HttpScraper):
    """Collect Wikipedia articles as raw documents."""

    def __init__(self, config: WikiScraperConfig | None = None) -> None:
        self._config = config or WikiScraperConfig()

    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        """Scrape from the XML dump or from the paginated REST API."""
        startedAt = time.monotonic()
        if self._config.useDump:
            scraped, saved, errors = self._scrapeFromDump(corpusRepo)
        else:
            scraped, saved, errors = self._scrapeFromApi(corpusRepo)
        return ScrapeResult(
            documentsScraped=scraped,
            documentsSaved=saved,
            errors=errors,
            durationSeconds=time.monotonic() - startedAt,
        )

    def _scrapeFromApi(
        self,
        corpusRepo: CorpusRepository,
    ) -> tuple[int, int, list[str]]:
        errors: list[str] = []
        scraped = 0
        saved = 0

        for language in self._config.languages:
            for _ in range(0, self._config.maxArticlesPerLang, API_PAGE_LIMIT):
                try:
                    payload = self._fetchJson(
                        WIKI_API_URL.format(language=language),
                        {
                            "action": "query",
                            "generator": "random",
                            "grnnamespace": 0,
                            "grnlimit": API_PAGE_LIMIT,
                            "prop": "extracts",
                            "explaintext": 1,
                            "exintro": 0,
                            "format": "json",
                            "formatversion": 2,
                        },
                    )
                except RiahAppError as error:
                    errors.append(str(error))
                    break

                pages = payload.get("query", {}).get("pages", [])
                pageList = pages.values() if isinstance(pages, dict) else pages
                batch: list[RawDocument] = []
                for page in pageList:
                    text = page.get("extract", "")
                    scraped += 1
                    if len(text) < self._config.minArticleLength:
                        continue
                    title = page.get("title", "")
                    batch.append(
                        RawDocument.create(
                            source="wikipedia",
                            url=f"https://{language}.wikipedia.org/wiki/{title}",
                            language=language,
                            text=text,
                            metadata={"title": title, "pageId": page.get("pageid")},
                        )
                    )
                if batch:
                    saved += corpusRepo.saveRaw(batch)

        return scraped, saved, errors

    def _scrapeFromDump(
        self,
        corpusRepo: CorpusRepository,
    ) -> tuple[int, int, list[str]]:
        dumpPath = self._config.dumpPath
        if dumpPath is None or not dumpPath.exists():
            raise ValidationError(
                "dumpPath est requis pour scraper depuis un dump Wikipedia",
                details={"dumpPath": str(dumpPath)},
            )

        errors: list[str] = []
        scraped = 0
        saved = 0
        batch: list[RawDocument] = []
        language = self._config.languages[0]

        for _, element in ElementTree.iterparse(dumpPath, events=("end",)):
            if not element.tag.endswith("page"):
                continue
            title = element.findtext("{*}title", default="")
            revisionText = element.find(".//{*}revision/{*}text")
            text = revisionText.text if revisionText is not None and revisionText.text else ""
            element.clear()
            scraped += 1
            if len(text) < self._config.minArticleLength:
                if scraped >= self._config.maxArticlesPerLang:
                    break
                continue
            batch.append(
                RawDocument.create(
                    source="wikipedia",
                    url=f"https://{language}.wikipedia.org/wiki/{title}",
                    language=language,
                    text=text,
                    metadata={"title": title, "dumpDate": self._config.dumpDate},
                )
            )
            if len(batch) >= WIKI_BATCH_SIZE:
                saved += corpusRepo.saveRaw(batch)
                batch = []
            if scraped >= self._config.maxArticlesPerLang:
                break

        if batch:
            saved += corpusRepo.saveRaw(batch)
        return scraped, saved, errors
