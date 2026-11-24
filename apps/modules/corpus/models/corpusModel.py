# apps/modules/corpus/models/corpusModel.py
"""Corpus Module - Domain Models"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class RawDocument:
    """Immutable document exactly as scraped from a source."""

    id: str
    source: str
    sourceUrl: str
    language: str
    text: str
    metadata: dict[str, Any]
    scrapedAt: datetime
    contentHash: str = ""

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("RawDocument.text ne peut pas etre vide")
        if not self.contentHash:
            contentHash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
            object.__setattr__(self, "contentHash", contentHash)

    @classmethod
    def create(
        cls,
        source: str,
        url: str,
        language: str,
        text: str,
        metadata: dict[str, Any],
    ) -> RawDocument:
        """Build a new document with a generated id, timestamp and content hash."""
        return cls(
            id=str(uuid.uuid4()),
            source=source,
            sourceUrl=url,
            language=language,
            text=text,
            metadata=metadata,
            scrapedAt=datetime.now(timezone.utc),
        )

    def toDict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "sourceUrl": self.sourceUrl,
            "language": self.language,
            "text": self.text,
            "metadata": self.metadata,
            "scrapedAt": self.scrapedAt.isoformat(),
            "contentHash": self.contentHash,
        }

    @classmethod
    def fromDict(cls, data: dict[str, Any]) -> RawDocument:
        """Rebuild a document from its serialized form."""
        return cls(
            id=data["id"],
            source=data["source"],
            sourceUrl=data["sourceUrl"],
            language=data["language"],
            text=data["text"],
            metadata=data.get("metadata", {}),
            scrapedAt=datetime.fromisoformat(data["scrapedAt"]),
            contentHash=data.get("contentHash", ""),
        )


@dataclass(frozen=True)
class CleanDocument:
    """Document after cleaning, normalization and quality scoring."""

    id: str
    source: str
    language: str
    text: str
    qualityScore: float
    tokenCount: int
    cleanedAt: datetime

    def toDict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "language": self.language,
            "text": self.text,
            "qualityScore": self.qualityScore,
            "tokenCount": self.tokenCount,
            "cleanedAt": self.cleanedAt.isoformat(),
        }

    @classmethod
    def fromDict(cls, data: dict[str, Any]) -> CleanDocument:
        """Rebuild a document from its serialized form."""
        return cls(
            id=data["id"],
            source=data["source"],
            language=data["language"],
            text=data["text"],
            qualityScore=float(data["qualityScore"]),
            tokenCount=int(data["tokenCount"]),
            cleanedAt=datetime.fromisoformat(data["cleanedAt"]),
        )


@dataclass(frozen=True)
class ShardInfo:
    """Metadata describing one binary token shard."""

    shardId: int
    filePath: Path
    indexPath: Path
    documentCount: int
    tokenCount: int
    languages: list[str]


@dataclass(frozen=True)
class CorpusStats:
    """Aggregated corpus statistics."""

    totalDocuments: int
    totalTokens: int
    totalSizeBytes: int
    languages: dict[str, int]


@dataclass(frozen=True)
class CorpusDatasetSummary:
    """One exported markdown corpus, grouped by source."""

    source: str
    languages: list[str]
    documentCount: int
    totalSizeBytes: int
    updatedAt: datetime
    path: str

    def toDict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "source": self.source,
            "languages": self.languages,
            "documentCount": self.documentCount,
            "totalSizeBytes": self.totalSizeBytes,
            "updatedAt": self.updatedAt.isoformat(),
            "path": self.path,
        }


@dataclass(frozen=True)
class ScrapeSourceDescription:
    """Scraping source exposed to the dashboard."""

    id: str
    label: str
    description: str
    languages: list[str]


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for a full corpus pipeline run."""

    outputDir: Path
    shardSizeTokens: int = 100_000_000
    tokenizerPath: Path = Path("data/tokenizer/tokenizer.json")
    numWorkers: int = 4
    batchSize: int = 1000
    resumeFromStep: str | None = None
    sources: list[str] = field(default_factory=lambda: ["wikipedia"])
    languages: list[str] = field(default_factory=lambda: ["fr"])
    maxArticlesPerLang: int = 1000


@dataclass(frozen=True)
class WikiScraperConfig:
    """Wikipedia scraping options."""

    languages: list[str] = field(default_factory=lambda: ["fr", "en"])
    maxArticlesPerLang: int = 100_000
    useDump: bool = True
    dumpDate: str = "latest"
    dumpPath: Path | None = None
    minArticleLength: int = 500


@dataclass(frozen=True)
class BibleScraperConfig:
    """Bible scraping options."""

    source: str = "bible"
    languages: list[str] = field(default_factory=lambda: ["fr", "en"])
    translationsPerLang: dict[str, str] = field(
        default_factory=lambda: {"fr": "crampon", "en": "kjv"}
    )
    minArticleLength: int = 100


@dataclass(frozen=True)
class HtmlCleanerConfig:
    """HTML cleaning options."""

    removeTags: list[str] = field(
        default_factory=lambda: [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "button",
            "input",
        ]
    )
    keepLinks: bool = False
    preserveCode: bool = True


@dataclass(frozen=True)
class TextNormalizerConfig:
    """Text normalization options."""

    unicodeForm: str = "NFC"
    fixMojibake: bool = True
    collapseWhitespace: bool = True
    removeControlChars: bool = True
    minLineLength: int = 10


@dataclass(frozen=True)
class QualityFilterConfig:
    """Quality thresholds for corpus filtering."""

    minCharLength: int = 100
    maxCharLength: int = 1_000_000
    minWordCount: int = 20
    maxSymbolRatio: float = 0.3
    maxRepetitionRatio: float = 0.15
    targetLanguages: list[str] = field(default_factory=lambda: ["fr", "en"])


@dataclass(frozen=True)
class DeduplicatorConfig:
    """Exact and near-duplicate detection options."""

    exactDedup: bool = True
    minhashDedup: bool = True
    minhashNumPerm: int = 128
    minhashThreshold: float = 0.7
    ngramSize: int = 5
    batchSize: int = 100_000


@dataclass(frozen=True)
class ScrapeResult:
    """Outcome of one scraper run."""

    documentsScraped: int = 0
    documentsSaved: int = 0
    errors: list[str] = field(default_factory=list)
    durationSeconds: float = 0.0


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of one full pipeline run."""

    documentsScraped: int
    documentsCleaned: int
    documentsFiltered: int
    documentsDeduplicated: int
    shardsWritten: int
    totalTokens: int
    durationSeconds: float
    documentsExported: int = 0


class PipelineStartRequest(BaseModel):
    """HTTP payload used to start a corpus pipeline."""

    outputDir: str = "data/corpus"
    shardSizeTokens: int = Field(default=100_000_000, ge=1_000)
    tokenizerPath: str = "data/tokenizer/tokenizer.json"
    numWorkers: int = Field(default=4, ge=1, le=64)
    batchSize: int = Field(default=1000, ge=1)
    resumeFromStep: str | None = None
    sources: list[str] = Field(default_factory=lambda: ["wikipedia"], min_length=1)
    languages: list[str] = Field(default_factory=lambda: ["fr"], min_length=1)
    maxArticlesPerLang: int = Field(default=1000, ge=1, le=1_000_000)

    def toPipelineConfig(self) -> PipelineConfig:
        """Convert the validated request into a domain configuration."""
        return PipelineConfig(
            outputDir=Path(self.outputDir),
            shardSizeTokens=self.shardSizeTokens,
            tokenizerPath=Path(self.tokenizerPath),
            numWorkers=self.numWorkers,
            batchSize=self.batchSize,
            resumeFromStep=self.resumeFromStep,
            sources=self.sources,
            languages=self.languages,
            maxArticlesPerLang=self.maxArticlesPerLang,
        )
