# apps/modules/model/pipelines/shardedDataset.py
"""Iterable dataset over the uint16 token shards produced by the tokenizer module."""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict

import numpy as np
import torch
from torch.utils.data import IterableDataset, get_worker_info

SHARD_FILE_SUFFIX = ".bin"
INDEX_FILE_SUFFIX = ".idx"
BYTES_PER_TOKEN = 2  # uint16


class ShardEntry(TypedDict):
    """One document inside a shard index file."""

    documentId: str
    offset: int
    length: int


class ShardedTokenDataset(IterableDataset[dict[str, torch.Tensor]]):
    """Stream `(input_ids, labels)` windows from one or more binary shards.

    Every window holds `seqLen` input tokens and the same amount of labels
    shifted by one position, so `labels[t]` is the token that follows
    `input_ids[t]`. Windows never cross a document boundary.
    """

    def __init__(
        self,
        shardPaths: list[Path] | list[str],
        seqLen: int,
        shuffle: bool = False,
        seed: int = 42,
        epoch: int = 0,
        validate: bool = True,
    ) -> None:
        if seqLen < 1:
            raise ValueError("seqLen must be >= 1")
        if seed < 0:
            raise ValueError("seed must be >= 0")

        self._seqLen = seqLen
        self._shuffle = shuffle
        self._seed = seed
        self._epoch = epoch
        self._shardPaths = [self._resolveShardPath(Path(path)) for path in shardPaths]
        self._indexes: dict[Path, list[ShardEntry]] = {}
        self._tokenCounts: dict[Path, int] = {}
        if validate:
            for path in self._shardPaths:
                self._loadIndex(path)

    @property
    def seqLen(self) -> int:
        """Number of input tokens per window."""
        return self._seqLen

    @property
    def shardPaths(self) -> list[Path]:
        """Resolved `.bin` shard paths."""
        return list(self._shardPaths)

    @property
    def epoch(self) -> int:
        """Epoch used to derive the shuffling seed."""
        return self._epoch

    @property
    def totalTokens(self) -> int:
        """Number of tokens available across every shard."""
        return sum(self._loadTokenCount(path) for path in self._shardPaths)

    def setEpoch(self, epoch: int) -> None:
        """Select the epoch, which changes the deterministic shuffling order."""
        self._epoch = epoch

    def __len__(self) -> int:
        """Number of complete windows across every shard."""
        total = 0
        for path in self._shardPaths:
            for entry in self._loadIndex(path):
                total += max(0, (entry["length"] - 1) // self._seqLen)
        return total

    def __iter__(self) -> Iterator[dict[str, torch.Tensor]]:
        """Yield shuffled windows, splitting shards across data-loader workers."""
        order = list(range(len(self._shardPaths)))
        generator = random.Random(self._seed + self._epoch)
        if self._shuffle:
            generator.shuffle(order)

        worker = get_worker_info()
        if worker is not None and worker.num_workers > 1:
            order = order[worker.id :: worker.num_workers]

        for shardIndex in order:
            yield from self._iterateShard(shardIndex, generator)

    def _iterateShard(
        self,
        shardIndex: int,
        generator: random.Random,
    ) -> Iterator[dict[str, torch.Tensor]]:
        """Yield every window of one shard, optionally shuffling documents."""
        shardPath = self._shardPaths[shardIndex]
        tokenCount = self._loadTokenCount(shardPath)
        if tokenCount == 0:
            return

        entries = list(self._loadIndex(shardPath))
        if self._shuffle:
            generator.shuffle(entries)

        tokens = np.memmap(shardPath, dtype=np.uint16, mode="r")
        try:
            for entry in entries:
                windowCount = max(0, (entry["length"] - 1) // self._seqLen)
                for windowIndex in range(windowCount):
                    offset = entry["offset"] + windowIndex * self._seqLen
                    window = np.asarray(
                        tokens[offset : offset + self._seqLen + 1],
                        dtype=np.int64,
                    )
                    yield {
                        "input_ids": torch.from_numpy(window[:-1]),
                        "labels": torch.from_numpy(window[1:]),
                    }
        finally:
            del tokens

    def _resolveShardPath(self, path: Path) -> Path:
        """Normalize the suffix and check that the shard and its index exist."""
        if path.suffix != SHARD_FILE_SUFFIX:
            path = path.with_suffix(SHARD_FILE_SUFFIX)

        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Shard introuvable: {resolved}")
        indexPath = resolved.with_suffix(INDEX_FILE_SUFFIX)
        if not indexPath.is_file():
            raise FileNotFoundError(f"Index de shard introuvable: {indexPath}")
        return resolved

    def _loadTokenCount(self, shardPath: Path) -> int:
        """Return the number of uint16 tokens stored in a shard."""
        if shardPath not in self._tokenCounts:
            self._tokenCounts[shardPath] = shardPath.stat().st_size // BYTES_PER_TOKEN
        return self._tokenCounts[shardPath]

    def _loadIndex(self, shardPath: Path) -> list[ShardEntry]:
        """Read (and cache) the JSONL index of a shard."""
        cached = self._indexes.get(shardPath)
        if cached is not None:
            return cached

        tokenCount = self._loadTokenCount(shardPath)
        entries: list[ShardEntry] = []
        indexPath = shardPath.with_suffix(INDEX_FILE_SUFFIX)
        with indexPath.open("r", encoding="utf-8") as handle:
            for lineNumber, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                entry: ShardEntry = {
                    "documentId": str(payload["documentId"]),
                    "offset": int(payload["offset"]),
                    "length": int(payload["length"]),
                }
                end = entry["offset"] + entry["length"]
                if entry["offset"] < 0 or end > tokenCount:
                    raise ValueError(
                        "Index de shard incoherent "
                        f"({indexPath.name}, ligne {lineNumber}): "
                        f"{entry['offset']}+{entry['length']} > {tokenCount}"
                    )
                entries.append(entry)

        self._indexes[shardPath] = entries
        return entries
