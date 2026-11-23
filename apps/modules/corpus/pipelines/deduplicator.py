# apps/modules/corpus/pipelines/deduplicator.py
"""Exact and near-duplicate detection using MinHash signatures with LSH banding."""
from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from ..models.corpusModel import CleanDocument, DeduplicatorConfig

HASH_SIZE_BYTES = 8


class Deduplicator:
    """Track already seen content and reject exact or near duplicates."""

    def __init__(self, config: DeduplicatorConfig | None = None) -> None:
        self._config = config or DeduplicatorConfig()
        self._exactHashes: set[str] = set()
        self._bands: set[tuple[int, int]] = set()
        self._bandsCount, self._rowsCount = self._computeBandLayout()

    def filter(self, documents: Iterable[CleanDocument]) -> Iterator[CleanDocument]:
        """Yield only the documents that are not duplicates."""
        for document in documents:
            if not self.isDuplicate(document.text):
                yield document

    def isDuplicate(self, text: str) -> bool:
        """Return True when the text was already seen (exactly or approximately)."""
        if self._config.exactDedup:
            exactHash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if exactHash in self._exactHashes:
                return True
            self._exactHashes.add(exactHash)

        if not self._config.minhashDedup:
            return False

        signature = self._minhashSignature(text)
        isNearDuplicate = False
        for bandIndex in range(self._bandsCount):
            start = bandIndex * self._rowsCount
            bandSlice = tuple(signature[start:start + self._rowsCount])
            bandKey = int.from_bytes(
                hashlib.blake2b(repr(bandSlice).encode("utf-8"), digest_size=HASH_SIZE_BYTES).digest(),
                "little",
            )
            band = (bandIndex, bandKey)
            if band in self._bands:
                isNearDuplicate = True
            self._bands.add(band)
        return isNearDuplicate

    def _computeBandLayout(self) -> tuple[int, int]:
        """Pick the (bands, rows) layout whose S-curve is closest to the threshold."""
        numPerm = self._config.minhashNumPerm
        bestBands = 1
        bestRows = numPerm
        bestError = float("inf")
        for rows in range(1, numPerm + 1):
            if numPerm % rows != 0:
                continue
            bands = numPerm // rows
            error = abs((1.0 / bands) ** (1.0 / rows) - self._config.minhashThreshold)
            if error < bestError:
                bestBands = bands
                bestRows = rows
                bestError = error
        return bestBands, bestRows

    def _minhashSignature(self, text: str) -> list[int]:
        shingles = self._shingles(text)
        signature: list[int] = []
        for seed in range(self._config.minhashNumPerm):
            seedBytes = seed.to_bytes(4, "little")
            minimum = min(
                int.from_bytes(
                    hashlib.blake2b(
                        shingle,
                        digest_size=HASH_SIZE_BYTES,
                        key=seedBytes,
                    ).digest(),
                    "little",
                )
                for shingle in shingles
            )
            signature.append(minimum)
        return signature

    def _shingles(self, text: str) -> set[bytes]:
        words = text.split()
        size = self._config.ngramSize
        if len(words) < size:
            return {text.encode("utf-8")}
        return {
            " ".join(words[index:index + size]).encode("utf-8")
            for index in range(len(words) - size + 1)
        }
