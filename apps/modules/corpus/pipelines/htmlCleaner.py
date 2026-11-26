# apps/modules/corpus/pipelines/htmlCleaner.py
"""Convert HTML pages to plain text without third-party dependencies."""

from __future__ import annotations

from html.parser import HTMLParser

from ..models.corpusModel import HtmlCleanerConfig

BLOCK_TAGS = {
    "p",
    "div",
    "br",
    "li",
    "tr",
    "td",
    "th",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "section",
    "article",
    "blockquote",
    "pre",
    "table",
}


class _TextExtractor(HTMLParser):
    """Collect visible text while skipping unwanted tags."""

    def __init__(self, removeTags: set[str], keepLinks: bool) -> None:
        super().__init__(convert_charrefs=True)
        self._removeTags = removeTags
        self._keepLinks = keepLinks
        self._skipDepth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._removeTags:
            self._skipDepth += 1
            return
        if self._keepLinks and tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._chunks.append(f" {href} ")
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._removeTags:
            if self._skipDepth > 0:
                self._skipDepth -= 1
            return
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skipDepth == 0 and data:
            self._chunks.append(data)

    def getText(self) -> str:
        return "".join(self._chunks)


class HtmlCleaner:
    """Strip markup, scripts and navigation from an HTML document."""

    def __init__(self, config: HtmlCleanerConfig | None = None) -> None:
        self._config = config or HtmlCleanerConfig()

    def clean(self, html: str) -> str:
        """Return the visible text of the page, one block per line."""
        if not html:
            return ""
        extractor = _TextExtractor(set(self._config.removeTags), self._config.keepLinks)
        extractor.feed(html)
        extractor.close()
        lines = (line.strip() for line in extractor.getText().splitlines())
        return "\n".join(line for line in lines if line)
