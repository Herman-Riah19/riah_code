# apps/modules/corpus/pipelines/valtortaScraper.py
"""Maria Valtorta scraper - collects the French revelations from the
public maria-valtorta.org website.

The website publishes each tome as an ``index.htm`` table of contents plus one
HTML page per chapter. Chapter pages are windows-1252 encoded and wrap their
content in ``<p>`` elements.
"""
from __future__ import annotations

import re
import time
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from ..models.corpusModel import BibleScraperConfig, RawDocument, ScrapeResult
from ..repositories.corpusRepository import CorpusRepository
from .httpScraper import HttpScraper

VALTORTA_BASE_URL = "https://www.maria-valtorta.org/Publication"
VALTORTA_TOMES: dict[str, str] = {
    "TOME%2001": "01",
    "TOME%2002": "02",
    "TOME%2003": "03",
    "TOME%2004": "04",
}
CHAPTER_LINK_PATTERN = re.compile(r"^(?P<prefix>\d{2})-(?P<number>\d{3})\.htm$")
REQUEST_DELAY_SECONDS = 0.2
VALTORTA_SAVE_BATCH_SIZE = 50
TITLE_MAX_LENGTH = 200

NAVIGATION_PARAGRAPHS = frozenset(
    {
        "Se reperer",
        "Se repérer",
        "Consulter la Bible en ligne",
        "Aller sur le forum partage",
        "Aller sur le forum partagé",
        "Qui sommes-nous ?",
        "Qui sommes-nous ?",
    }
)
SKIPPED_PREFIXES = (
    "Ancienne edition",
    "Ancienne édition",
    "Nouvelle edition",
    "Nouvelle édition",
)


class _ChapterLinkParser(HTMLParser):
    """Collect chapter links belonging to one tome."""

    def __init__(self, tomePrefix: str) -> None:
        super().__init__()
        self._tomePrefix = tomePrefix
        self._seen: set[str] = set()
        self.chapters: list[tuple[int, str]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "a":
            return
        href = next((value for name, value in attrs if name == "href"), None)
        if href is None:
            return
        match = CHAPTER_LINK_PATTERN.match(href)
        if match is None or match.group("prefix") != self._tomePrefix:
            return
        if href in self._seen:
            return
        self._seen.add(href)
        self.chapters.append((int(match.group("number")), href))


class _ParagraphParser(HTMLParser):
    """Extract normalized text from every ``<p>`` element."""

    def __init__(self) -> None:
        super().__init__()
        self.paragraphs: list[str] = []
        self._inParagraph = False
        self._buffer: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag == "p":
            self._inParagraph = True
            self._buffer = []
        elif tag == "br" and self._inParagraph:
            self._buffer.append(" ")

    def handle_data(self, data: str) -> None:
        if self._inParagraph:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "p" or not self._inParagraph:
            return
        text = unescape("".join(self._buffer))
        text = re.sub(r"\s+", " ", text).strip()
        self.paragraphs.append(text)
        self._inParagraph = False
        self._buffer = []


class ValtortaScraper(HttpScraper):
    """Collect Maria Valtorta's revelations, one document per chapter."""

    def __init__(self, config: BibleScraperConfig | None = None) -> None:
        self._config = config or BibleScraperConfig(
            source="valtorta",
            languages=["fr"],
        )

    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        """Walk every tome index, then fetch and persist each chapter."""
        startedAt = time.monotonic()
        errors: list[str] = []
        scraped = 0
        saved = 0
        batch: list[RawDocument] = []

        for tome, prefix in VALTORTA_TOMES.items():
            indexUrl = f"{VALTORTA_BASE_URL}/{tome}/index.htm"
            try:
                indexHtml = self._fetchText(
                    indexUrl,
                    ("cp1252", "latin-1"),
                )
            except Exception as error:  # noqa: BLE001 - report and continue
                errors.append(f"{tome}: index inaccessible ({error})")
                continue

            chapters = self._parseIndex(indexHtml, prefix)
            if not chapters:
                errors.append(f"{tome}: aucun chapitre trouve dans l'index")
                continue

            for chapterNumber, link in chapters:
                try:
                    chapterUrl = f"{VALTORTA_BASE_URL}/{tome}/{link}"
                    chapterHtml = self._fetchText(
                        chapterUrl,
                        ("cp1252", "latin-1"),
                    )
                    content, title = self._extractChapter(chapterHtml)
                    if len(content) < self._config.minArticleLength:
                        continue

                    scraped += 1
                    batch.append(
                        RawDocument.create(
                            source=self._config.source,
                            url=chapterUrl,
                            language="fr",
                            text=content,
                            metadata={
                                "tome": int(prefix),
                                "chapter": chapterNumber,
                                "title": title,
                                "source_type": "valtorta",
                            },
                        )
                    )
                    if len(batch) >= VALTORTA_SAVE_BATCH_SIZE:
                        saved += corpusRepo.saveRaw(batch)
                        batch = []
                except Exception as error:  # noqa: BLE001 - report and continue
                    errors.append(f"{tome}/{link}: {error}")
                finally:
                    time.sleep(REQUEST_DELAY_SECONDS)

        if batch:
            saved += corpusRepo.saveRaw(batch)

        return ScrapeResult(
            documentsScraped=scraped,
            documentsSaved=saved,
            errors=errors,
            durationSeconds=time.monotonic() - startedAt,
        )

    @staticmethod
    def _parseIndex(html: str, tomePrefix: str) -> list[tuple[int, str]]:
        """Return ``(chapterNumber, link)`` pairs for the requested tome."""
        parser = _ChapterLinkParser(tomePrefix)
        parser.feed(html)
        return sorted(parser.chapters, key=lambda chapter: chapter[0])

    def _extractChapter(self, html: str) -> tuple[str, str]:
        """Extract the readable revelation body and a short chapter title."""
        parser = _ParagraphParser()
        parser.feed(html)
        body = self._selectBody(parser.paragraphs)
        title = body[0][:TITLE_MAX_LENGTH] if body else ""
        return "\n\n".join(body), title

    @staticmethod
    def _selectBody(paragraphs: list[str]) -> list[str]:
        """Drop navigation, edition notices and footnotes around the body."""
        start = 0
        for index, paragraph in enumerate(paragraphs):
            if "Accueil" in paragraph and "Sommaire" in paragraph:
                start = index + 1
                break

        end = len(paragraphs)
        for index in range(start, len(paragraphs)):
            paragraph = paragraphs[index]
            if paragraph.startswith("[") or "Haut de page" in paragraph:
                end = index
                break

        body: list[str] = []
        for paragraph in paragraphs[start:end]:
            if not paragraph or paragraph in NAVIGATION_PARAGRAPHS:
                continue
            if paragraph.startswith(SKIPPED_PREFIXES):
                continue
            body.append(paragraph)
        return body
