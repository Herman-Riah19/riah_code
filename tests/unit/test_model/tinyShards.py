# tests/unit/test_model/tinyShards.py
"""Helpers to build tiny uint16 token shards for model tests."""

from __future__ import annotations

import json
from array import array
from pathlib import Path


def makeTokenDocuments(
    documentCount: int = 6,
    documentLength: int = 40,
    vocabSize: int = 64,
    seed: int = 7,
) -> list[list[int]]:
    """Return deterministic token ids shaped like a small corpus."""
    documents: list[list[int]] = []
    value = seed
    for _ in range(documentCount):
        document: list[int] = []
        for _ in range(documentLength):
            value = (value * 31 + 17) % vocabSize
            document.append(value)
        documents.append(document)
    return documents


def writeTokenShard(
    shardPath: Path | str,
    documents: list[list[int]],
    vocabSize: int = 64,
) -> Path:
    """Write a `.bin` shard plus its JSONL `.idx` index."""
    path = Path(shardPath)
    path.parent.mkdir(parents=True, exist_ok=True)

    tokens: list[int] = []
    entries: list[dict[str, int | str]] = []
    for index, document in enumerate(documents):
        ids = [int(tokenId) % vocabSize for tokenId in document]
        if not ids:
            continue
        entries.append(
            {
                "documentId": f"doc-{index}",
                "offset": len(tokens),
                "length": len(ids),
            }
        )
        tokens.extend(ids)

    path.write_bytes(array("H", tokens).tobytes())
    path.with_suffix(".idx").write_text(
        "".join(json.dumps(entry) + "\n" for entry in entries),
        encoding="utf-8",
    )
    return path


def writeTinyShard(
    directory: Path | str,
    name: str = "shard_000001.bin",
    documentCount: int = 6,
    documentLength: int = 40,
    vocabSize: int = 64,
    seed: int = 7,
) -> Path:
    """Write one tiny shard into `directory` and return its path."""
    documents = makeTokenDocuments(
        documentCount=documentCount,
        documentLength=documentLength,
        vocabSize=vocabSize,
        seed=seed,
    )
    return writeTokenShard(Path(directory) / name, documents, vocabSize=vocabSize)


__all__ = ["makeTokenDocuments", "writeTokenShard", "writeTinyShard"]
