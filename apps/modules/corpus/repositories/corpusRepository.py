# apps/modules/corpus/repositories/corpusRepository.py
"""Corpus repository - local JSONL(gzip) files plus a SQLite shard index."""
from __future__ import annotations

import json
import random
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Iterator

from apps.modules.shared.storage.fileStorage import FileStorage
from apps.modules.shared.storage.sqliteStorage import SQLiteStorage

from ..models.corpusModel import (
    CleanDocument,
    CorpusDatasetSummary,
    CorpusStats,
    RawDocument,
    ShardInfo,
)

JSONL_SUFFIX = ".jsonl.gz"
MARKDOWN_SUFFIX = ".md"
DEFAULT_SPLIT = "train"
SAMPLE_SEED = 42

SHARD_SCHEMA = """
CREATE TABLE IF NOT EXISTS shards (
    shardId INTEGER PRIMARY KEY,
    filePath TEXT NOT NULL,
    indexPath TEXT NOT NULL,
    documentCount INTEGER NOT NULL,
    tokenCount INTEGER NOT NULL,
    languages TEXT NOT NULL,
    split TEXT NOT NULL DEFAULT 'train'
);
"""


class CorpusRepository:
    """Persistence layer for raw documents, clean documents and shards."""

    def __init__(self, baseDir: Path) -> None:
        self._baseDir = baseDir
        self._rawDir = baseDir / "raw"
        self._cleanDir = baseDir / "clean"
        self._shardDir = baseDir / "shards"
        self._rawStorage = FileStorage(self._rawDir)
        self._cleanStorage = FileStorage(self._baseDir)
        self._db = SQLiteStorage(baseDir / "corpus_index.sqlite")
        self._initDirs()
        self._initSchema()

    def _initDirs(self) -> None:
        for path in (self._rawDir, self._cleanDir, self._shardDir):
            path.mkdir(parents=True, exist_ok=True)

    def _initSchema(self) -> None:
        self._db.executeScript(SHARD_SCHEMA)

    @staticmethod
    def _dayPartition() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def saveRaw(self, docs: list[RawDocument]) -> int:
        """Append raw documents as gzipped JSONL, partitioned by source and day."""
        if not docs:
            return 0
        grouped: dict[str, list[RawDocument]] = {}
        for document in docs:
            grouped.setdefault(document.source, []).append(document)

        saved = 0
        for source, sourceDocuments in grouped.items():
            filePath = self._rawDir / source / f"{self._dayPartition()}{JSONL_SUFFIX}"
            with self._rawStorage.writeJsonl(filePath, compress=True, append=True) as writeLine:
                for document in sourceDocuments:
                    writeLine(document.toDict())
                    saved += 1
        return saved

    def loadRaw(
        self,
        source: str | None = None,
        limit: int | None = None,
    ) -> Iterator[RawDocument]:
        """Stream raw documents, optionally restricted to one source."""
        pattern = f"{source}/*{JSONL_SUFFIX}" if source else f"*/*{JSONL_SUFFIX}"
        loaded = 0
        for filePath in sorted(self._rawDir.glob(pattern)):
            for record in self._rawStorage.readJsonl(filePath, compress=True):
                yield RawDocument.fromDict(record)
                loaded += 1
                if limit is not None and loaded >= limit:
                    return

    def saveClean(self, docs: Iterable[CleanDocument]) -> int:
        """Append clean documents as gzipped JSONL, partitioned by language."""
        saved = 0
        with ExitStack() as stack:
            writers: dict[str, Callable[[dict], None]] = {}
            for document in docs:
                writer = writers.get(document.language)
                if writer is None:
                    filePath = (
                        self._cleanDir
                        / document.language
                        / f"{self._dayPartition()}{JSONL_SUFFIX}"
                    )
                    writer = stack.enter_context(
                        self._cleanStorage.writeJsonl(
                            filePath,
                            compress=True,
                            append=True,
                        )
                    )
                    writers[document.language] = writer
                writer(document.toDict())
                saved += 1
        return saved

    def loadClean(self, languages: list[str] | None = None) -> Iterator[CleanDocument]:
        """Stream clean documents, optionally restricted to some languages."""
        patterns = (
            [f"{language}/*{JSONL_SUFFIX}" for language in languages]
            if languages
            else [f"*/*{JSONL_SUFFIX}"]
        )
        for pattern in patterns:
            for filePath in sorted(self._cleanDir.glob(pattern)):
                for record in self._cleanStorage.readJsonl(filePath, compress=True):
                    yield CleanDocument.fromDict(record)

    def sampleClean(
        self,
        sampleSize: int,
        languages: list[str] | None = None,
    ) -> Iterator[CleanDocument]:
        """Reservoir sample of clean documents, used to train the tokenizer."""
        reservoir: list[CleanDocument] = []
        generator = random.Random(SAMPLE_SEED)
        for index, document in enumerate(self.loadClean(languages)):
            if index < sampleSize:
                reservoir.append(document)
                continue
            swapIndex = generator.randint(0, index)
            if swapIndex < sampleSize:
                reservoir[swapIndex] = document
        yield from reservoir

    def saveShardInfo(self, shards: list[ShardInfo]) -> None:
        """Upsert shard metadata into the SQLite index."""
        if not shards:
            return
        paramsList = [
            (
                shard.shardId,
                str(shard.filePath),
                str(shard.indexPath),
                shard.documentCount,
                shard.tokenCount,
                json.dumps(shard.languages, ensure_ascii=False),
                DEFAULT_SPLIT,
            )
            for shard in shards
        ]
        self._db.executemany(
            """
            INSERT INTO shards
                (shardId, filePath, indexPath, documentCount, tokenCount, languages, split)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(shardId) DO UPDATE SET
                filePath = excluded.filePath,
                indexPath = excluded.indexPath,
                documentCount = excluded.documentCount,
                tokenCount = excluded.tokenCount,
                languages = excluded.languages,
                split = excluded.split
            """,
            paramsList,
        )

    def getShardsForTraining(self, split: str = DEFAULT_SPLIT) -> list[ShardInfo]:
        """Return shards belonging to a dataset split, ordered by shard id."""
        rows = self._db.fetchAll(
            "SELECT shardId, filePath, indexPath, documentCount, tokenCount, languages "
            "FROM shards WHERE split = ? ORDER BY shardId",
            (split,),
        )
        return [
            ShardInfo(
                shardId=int(row["shardId"]),
                filePath=Path(row["filePath"]),
                indexPath=Path(row["indexPath"]),
                documentCount=int(row["documentCount"]),
                tokenCount=int(row["tokenCount"]),
                languages=json.loads(row["languages"]),
            )
            for row in rows
        ]

    def getGlobalStats(self) -> CorpusStats:
        """Aggregate document, token, size and language statistics."""
        rows = self._db.fetchAll(
            "SELECT documentCount, tokenCount, languages, filePath FROM shards"
        )
        totalDocuments = 0
        totalTokens = 0
        totalSizeBytes = 0
        languages: dict[str, int] = {}

        for row in rows:
            documentCount = int(row["documentCount"])
            totalDocuments += documentCount
            totalTokens += int(row["tokenCount"])
            shardPath = Path(row["filePath"])
            if shardPath.exists():
                totalSizeBytes += shardPath.stat().st_size
            for language in json.loads(row["languages"]):
                languages[language] = languages.get(language, 0) + documentCount

        if not rows:
            for document in self.loadClean():
                totalDocuments += 1
                totalTokens += document.tokenCount
                languages[document.language] = languages.get(document.language, 0) + 1

        return CorpusStats(
            totalDocuments=totalDocuments,
            totalTokens=totalTokens,
            totalSizeBytes=totalSizeBytes,
            languages=languages,
        )

    def getMarkdownDir(self) -> Path:
        """Return (and create) the directory holding exported `.md` corpora."""
        markdownDir = self._baseDir / "markdown"
        markdownDir.mkdir(parents=True, exist_ok=True)
        return markdownDir

    def getShardDir(self) -> Path:
        """Return (and create) the directory holding encoded token shards."""
        self._shardDir.mkdir(parents=True, exist_ok=True)
        return self._shardDir

    def listMarkdownCorpora(
        self, extraDirs: list[Path] | None = None
    ) -> list[CorpusDatasetSummary]:
        """Group exported markdown files by source, with size and freshness.

        Includes the default markdown directory plus any extra directories
        (for example ``data/bible`` for public-domain Bible/Valtorta texts).
        """
        dirs: list[Path] = [self.getMarkdownDir()]
        dirs.extend(extraDirs or [])
        filesBySource: dict[str, list[Path]] = {}
        sourceDir: dict[str, Path] = {}
        for markdownDir in dirs:
            for filePath in markdownDir.glob(f"*/*/*{MARKDOWN_SUFFIX}"):
                source = filePath.parent.parent.name
                filesBySource.setdefault(source, []).append(filePath)
                sourceDir.setdefault(source, markdownDir)

        summaries: list[CorpusDatasetSummary] = []
        for source, files in sorted(filesBySource.items()):
            stats = [filePath.stat() for filePath in files]
            latestMtime = max(stat.st_mtime for stat in stats)
            summaries.append(
                CorpusDatasetSummary(
                    source=source,
                    languages=sorted({filePath.parent.name for filePath in files}),
                    documentCount=len(files),
                    totalSizeBytes=sum(stat.st_size for stat in stats),
                    updatedAt=datetime.fromtimestamp(latestMtime, tz=timezone.utc),
                    path=str(sourceDir[source] / source),
                )
            )
        return summaries
