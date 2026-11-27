# apps/modules/corpus/pipelines/pipelineOrchestrator.py
"""Orchestrate the full corpus pipeline: scrape, clean, filter, dedup, shard, index."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from ...shared.kernel.exceptions import ValidationError
from ..models.corpusModel import (
    CleanDocument,
    PipelineConfig,
    PipelineResult,
    ShardInfo,
)
from ..repositories.corpusRepository import CorpusRepository
from .baseScraper import BaseScraper
from .deduplicator import Deduplicator
from .htmlCleaner import HtmlCleaner
from .markdownExporter import MarkdownExporter
from .qualityFilter import QualityFilter
from .shardWriter import ShardWriter
from .textNormalizer import TextNormalizer

STEP_SCRAPE = "scrape"
STEP_CLEAN = "clean"
STEP_FILTER = "filter"
STEP_DEDUP = "dedup"
STEP_SHARD = "shard"
STEP_INDEX = "index"
STEP_ORDER = (STEP_SCRAPE, STEP_CLEAN, STEP_FILTER, STEP_DEDUP, STEP_SHARD, STEP_INDEX)


class PipelineOrchestrator:
    """Run every pipeline stage in order, checkpointing each completed stage."""

    def __init__(
        self,
        scrapers: list[BaseScraper],
        cleaner: HtmlCleaner,
        normalizer: TextNormalizer,
        qualityFilter: QualityFilter,
        deduplicator: Deduplicator,
        shardWriter: ShardWriter,
        corpusRepo: CorpusRepository,
        checkpointDir: Path,
        markdownExporter: MarkdownExporter | None = None,
        markdownDir: Path | None = None,
        markdownDirs: dict[str, Path] | None = None,
    ) -> None:
        self._scrapers = scrapers
        self._cleaner = cleaner
        self._normalizer = normalizer
        self._qualityFilter = qualityFilter
        self._deduplicator = deduplicator
        self._shardWriter = shardWriter
        self._corpusRepo = corpusRepo
        self._checkpointDir = checkpointDir
        self._markdownExporter = markdownExporter
        self._markdownDir = markdownDir
        self._markdownDirs = markdownDirs or {}

    def runFullPipeline(self, config: PipelineConfig) -> PipelineResult:
        """Execute the pipeline, optionally resuming at a named stage."""
        startedAt = time.monotonic()
        resumeStep = config.resumeFromStep or STEP_SCRAPE
        if resumeStep not in STEP_ORDER:
            raise ValidationError(
                "Etape de reprise inconnue",
                details={"resumeFromStep": resumeStep, "allowedSteps": list(STEP_ORDER)},
            )
        startIndex = STEP_ORDER.index(resumeStep)
        config.outputDir.mkdir(parents=True, exist_ok=True)
        self._checkpointDir.mkdir(parents=True, exist_ok=True)

        documentsScraped = 0
        if startIndex <= STEP_ORDER.index(STEP_SCRAPE):
            documentsScraped = self._scrape(config)
            self._saveCheckpoint(STEP_SCRAPE, {"documentsScraped": documentsScraped})

        counters = {
            "documentsCleaned": 0,
            "documentsFiltered": 0,
            "documentsDeduplicated": 0,
            "documentsExported": 0,
        }
        if startIndex <= STEP_ORDER.index(STEP_DEDUP):
            counters = self._cleanFilterDedup()
            self._saveCheckpoint(STEP_DEDUP, counters)

        shards = self._shard(config)
        self._corpusRepo.saveShardInfo(shards)
        self._saveCheckpoint(STEP_SHARD, {"shardsWritten": len(shards)})

        totalTokens = sum(int(getattr(shard, "tokenCount", 0)) for shard in shards)
        return PipelineResult(
            documentsScraped=documentsScraped,
            documentsCleaned=counters["documentsCleaned"],
            documentsFiltered=counters["documentsFiltered"],
            documentsDeduplicated=counters["documentsDeduplicated"],
            documentsExported=counters["documentsExported"],
            shardsWritten=len(shards),
            totalTokens=totalTokens,
            durationSeconds=time.monotonic() - startedAt,
        )

    def _scrape(self, config: PipelineConfig) -> int:
        totalScraped = 0
        for scraper in self._scrapers:
            result = scraper.scrape(self._corpusRepo)
            totalScraped += result.documentsScraped
        return int(totalScraped)

    def _cleanFilterDedup(self) -> dict[str, int]:
        counters = {
            "documentsCleaned": 0,
            "documentsFiltered": 0,
            "documentsDeduplicated": 0,
            "documentsExported": 0,
        }
        self._corpusRepo.saveClean(self._buildCleanDocuments(counters))
        return counters

    def _buildCleanDocuments(self, counters: dict[str, int]) -> Iterator[CleanDocument]:
        for rawDocument in self._corpusRepo.loadRaw():
            cleanedText = self._normalizer.normalize(self._cleaner.clean(rawDocument.text))
            if not cleanedText:
                counters["documentsFiltered"] += 1
                continue

            cleanDocument = CleanDocument(
                id=rawDocument.id,
                source=rawDocument.source,
                language=rawDocument.language,
                text=cleanedText,
                qualityScore=self._qualityFilter.score(cleanedText, rawDocument.language),
                tokenCount=len(cleanedText.split()),
                cleanedAt=datetime.now(UTC),
            )
            counters["documentsCleaned"] += 1

            if not self._qualityFilter.accepts(cleanDocument):
                counters["documentsFiltered"] += 1
                continue
            if self._deduplicator.isDuplicate(cleanDocument.text):
                counters["documentsDeduplicated"] += 1
                continue

            if self._markdownExporter is not None:
                markdownDir = self._markdownDirFor(cleanDocument.source)
                self._markdownExporter.exportDocument(cleanDocument, markdownDir)
                counters["documentsExported"] += 1

            yield cleanDocument

    def _markdownDirFor(self, source: str) -> Path:
        """Resolve the markdown destination directory for one source."""
        if source in self._markdownDirs:
            return self._markdownDirs[source]
        if self._markdownDir is not None:
            return self._markdownDir
        return self._corpusRepo.getMarkdownDir()

    def _shard(self, config: PipelineConfig) -> list[ShardInfo]:
        return self._shardWriter.writeShards(
            self._corpusRepo.loadClean(),
            config.outputDir,
            config.shardSizeTokens,
        )

    def _saveCheckpoint(self, step: str, payload: dict[str, int]) -> None:
        checkpointPath = self._checkpointDir / f"{step}.json"
        checkpointPath.write_text(
            json.dumps(
                {
                    "step": step,
                    "payload": payload,
                    "savedAt": datetime.now(UTC).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
