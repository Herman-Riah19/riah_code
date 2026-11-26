# apps/modules/corpus/pipelines/shardWriter.py
"""Write token shards as uint16 binaries with a JSONL document index."""

from __future__ import annotations

import json
from array import array
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from ..models.corpusModel import CleanDocument, ShardInfo

DEFAULT_SHARD_SIZE_TOKENS = 100_000_000
SHARD_FILE_SUFFIX = ".bin"
INDEX_FILE_SUFFIX = ".idx"
UINT16_MAX = 65_535


class _ShardBuffer:
    """Accumulates token ids and per-document offsets for one shard."""

    def __init__(self) -> None:
        self.tokenIds: list[int] = []
        self.entries: list[dict[str, str | int]] = []
        self.languages: set[str] = set()

    def add(self, document: CleanDocument, tokenIds: Sequence[int]) -> None:
        if not tokenIds:
            return
        offset = len(self.tokenIds)
        self.tokenIds.extend(tokenIds)
        self.entries.append({"documentId": document.id, "offset": offset, "length": len(tokenIds)})
        self.languages.add(document.language)

    def isEmpty(self) -> bool:
        return not self.entries

    def reset(self) -> None:
        self.tokenIds = []
        self.entries = []
        self.languages = set()


class ShardWriter:
    """Split encoded documents into binary shards plus their index files."""

    def __init__(self, encodeFn: Callable[[str], Sequence[int]] | None = None) -> None:
        self._encodeFn = encodeFn or self._encodeUtf8

    def writeShards(
        self,
        documents: Iterable[CleanDocument],
        outputDir: Path,
        shardSizeTokens: int = DEFAULT_SHARD_SIZE_TOKENS,
    ) -> list[ShardInfo]:
        """Encode documents and flush one shard each time the size limit is hit."""
        outputDir.mkdir(parents=True, exist_ok=True)
        shards: list[ShardInfo] = []
        buffer = _ShardBuffer()
        shardId = 0

        for document in documents:
            tokenIds = [tokenId & UINT16_MAX for tokenId in self._encodeFn(document.text)]
            buffer.add(document, tokenIds)
            if len(buffer.tokenIds) >= shardSizeTokens:
                shardId += 1
                shards.append(self._flushShard(shardId, buffer, outputDir))
                buffer.reset()

        if not buffer.isEmpty():
            shardId += 1
            shards.append(self._flushShard(shardId, buffer, outputDir))
            buffer.reset()

        return shards

    def _flushShard(
        self,
        shardId: int,
        buffer: _ShardBuffer,
        outputDir: Path,
    ) -> ShardInfo:
        shardPath = outputDir / f"shard_{shardId:06d}{SHARD_FILE_SUFFIX}"
        indexPath = outputDir / f"shard_{shardId:06d}{INDEX_FILE_SUFFIX}"

        with shardPath.open("wb") as shardFile:
            array("H", buffer.tokenIds).tofile(shardFile)

        with indexPath.open("w", encoding="utf-8") as indexFile:
            for entry in buffer.entries:
                indexFile.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return ShardInfo(
            shardId=shardId,
            filePath=shardPath,
            indexPath=indexPath,
            documentCount=len(buffer.entries),
            tokenCount=len(buffer.tokenIds),
            languages=sorted(buffer.languages),
        )

    def _encodeUtf8(self, text: str) -> list[int]:
        return list(text.encode("utf-8"))
