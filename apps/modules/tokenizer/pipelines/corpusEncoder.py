# apps/modules/tokenizer/pipelines/corpusEncoder.py
"""Encode clean documents into uint16 token shards indexed by document."""

from __future__ import annotations

import time
from collections.abc import Iterable, Iterator

from apps.modules.corpus.models.corpusModel import CleanDocument
from apps.modules.corpus.pipelines.shardWriter import ShardWriter
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository

from ..models.tokenizerModel import BPETokenizer, EncodedCorpusStats

DEFAULT_SHARD_SIZE_TOKENS = 100_000_000


class CorpusEncoder:
    """Stream clean documents through a tokenizer and persist binary shards."""

    def __init__(
        self,
        tokenizer: BPETokenizer,
        corpusRepo: CorpusRepository,
        shardWriter: ShardWriter | None = None,
        shardSizeTokens: int = DEFAULT_SHARD_SIZE_TOKENS,
    ) -> None:
        self._tokenizer = tokenizer
        self._corpusRepo = corpusRepo
        self._shardWriter = shardWriter or ShardWriter(tokenizer.encode)
        self._shardSizeTokens = shardSizeTokens

    def encodeCorpus(
        self,
        documents: Iterable[CleanDocument],
    ) -> EncodedCorpusStats:
        """Encode every document, write shards and update the shard index."""
        startedAt = time.perf_counter()
        languageDistribution: dict[str, int] = {}

        shards = self._shardWriter.writeShards(
            self._trackLanguages(documents, languageDistribution),
            self._corpusRepo.getShardDir(),
            self._shardSizeTokens,
        )
        self._corpusRepo.saveShardInfo(shards)

        totalDocuments = sum(shard.documentCount for shard in shards)
        totalTokens = sum(shard.tokenCount for shard in shards)

        return EncodedCorpusStats(
            totalTokens=totalTokens,
            totalDocuments=totalDocuments,
            shardCount=len(shards),
            avgTokensPerDoc=totalTokens / totalDocuments if totalDocuments else 0.0,
            languageDistribution=languageDistribution,
            durationSeconds=time.perf_counter() - startedAt,
        )

    @staticmethod
    def _trackLanguages(
        documents: Iterable[CleanDocument],
        languageDistribution: dict[str, int],
    ) -> Iterator[CleanDocument]:
        for document in documents:
            languageDistribution[document.language] = (
                languageDistribution.get(document.language, 0) + 1
            )
            yield document
