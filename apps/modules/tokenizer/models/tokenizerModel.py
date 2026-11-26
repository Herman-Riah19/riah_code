# apps/modules/tokenizer/models/tokenizerModel.py
"""Tokenizer Module - Domain models, BPE wrapper and HTTP schemas."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field
from tokenizers import Tokenizer as HFTokenizer

DEFAULT_SPECIAL_TOKENS: tuple[str, ...] = (
    "<|endoftext|>",
    "<|pad|>",
    "<|unk|>",
    "<|mask|>",
)


@dataclass(frozen=True)
class TokenizerConfig:
    """Immutable configuration used to train one BPE tokenizer."""

    vocabSize: int = 32_000
    minFrequency: int = 2
    specialTokens: tuple[str, ...] = DEFAULT_SPECIAL_TOKENS
    # Kept in the contract for compatibility: byte-level pre-tokenization
    # already guarantees full byte coverage, so no unknown token is emitted.
    byteFallback: bool = True
    addPrefixSpace: bool = True
    trimWhitespace: bool = False
    showProgress: bool = False
    numThreads: int = 4

    def configHash(self) -> str:
        """Return a stable short hash identifying this configuration."""
        payload = {
            "vocabSize": self.vocabSize,
            "minFrequency": self.minFrequency,
            "specialTokens": list(self.specialTokens),
            "byteFallback": self.byteFallback,
            "addPrefixSpace": self.addPrefixSpace,
            "trimWhitespace": self.trimWhitespace,
            "numThreads": self.numThreads,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]


@dataclass(frozen=True)
class VocabInfo:
    """Metadata describing a trained vocabulary."""

    vocabSize: int
    specialTokenIds: dict[str, int]
    compressionRatio: float
    oovRate: float
    trainedAt: datetime
    configHash: str

    def toDict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        return {
            "vocabSize": self.vocabSize,
            "specialTokenIds": dict(self.specialTokenIds),
            "compressionRatio": self.compressionRatio,
            "oovRate": self.oovRate,
            "trainedAt": self.trainedAt.isoformat(),
            "configHash": self.configHash,
        }

    @classmethod
    def fromDict(cls, data: dict[str, Any]) -> VocabInfo:
        """Rebuild vocabulary metadata from its serialized form."""
        return cls(
            vocabSize=int(data["vocabSize"]),
            specialTokenIds={
                str(token): int(tokenId)
                for token, tokenId in data.get("specialTokenIds", {}).items()
            },
            compressionRatio=float(data["compressionRatio"]),
            oovRate=float(data["oovRate"]),
            trainedAt=datetime.fromisoformat(data["trainedAt"]),
            configHash=str(data["configHash"]),
        )

    def toJson(self) -> str:
        """Serialize to the `vocab_info.json` payload."""
        return json.dumps(self.toDict(), ensure_ascii=False, indent=2)

    @classmethod
    def fromJson(cls, jsonStr: str) -> VocabInfo:
        """Parse the `vocab_info.json` payload."""
        return cls.fromDict(json.loads(jsonStr))


class BPETokenizer:
    """Runtime wrapper around a trained Hugging Face tokenizer."""

    def __init__(self, tokenizerPath: Path) -> None:
        self._tokenizerPath = tokenizerPath
        self._hfTokenizer = HFTokenizer.from_file(str(tokenizerPath))
        self._vocab = cast("dict[str, int]", self._hfTokenizer.get_vocab())
        self._idToToken = {tokenId: token for token, tokenId in self._vocab.items()}
        self._eosId = self._requireSpecialToken("<|endoftext|>")
        self._padId = self._requireSpecialToken("<|pad|>")
        self._unkId = self._requireSpecialToken("<|unk|>")

    def _requireSpecialToken(self, token: str) -> int:
        tokenId = self._vocab.get(token)
        if tokenId is None:
            raise ValueError(f"Token special absent du vocabulaire: {token}")
        return tokenId

    @property
    def tokenizerPath(self) -> Path:
        """Path of the underlying `tokenizer.json` file."""
        return self._tokenizerPath

    @property
    def vocabSize(self) -> int:
        """Number of tokens known by the tokenizer."""
        return len(self._vocab)

    @property
    def eosTokenId(self) -> int:
        """Identifier of the end-of-text token."""
        return self._eosId

    @property
    def padTokenId(self) -> int:
        """Identifier of the padding token."""
        return self._padId

    @property
    def unkTokenId(self) -> int:
        """Identifier of the unknown token."""
        return self._unkId

    def encode(self, text: str, addSpecialTokens: bool = True) -> list[int]:
        """Encode one text into token ids, appending EOS by default."""
        tokenIds = list(self._hfTokenizer.encode(text).ids)
        if addSpecialTokens:
            tokenIds.append(self._eosId)
        return tokenIds

    def encodeBatch(
        self,
        texts: list[str],
        addSpecialTokens: bool = True,
        padding: bool = True,
        maxLength: int | None = None,
    ) -> dict[str, list[list[int]]]:
        """Encode several texts, optionally truncating and padding them."""
        encodings = self._hfTokenizer.encode_batch(texts)
        tokenIds = [list(encoding.ids) for encoding in encodings]

        if addSpecialTokens:
            tokenIds = [sequence + [self._eosId] for sequence in tokenIds]

        if maxLength is not None:
            tokenIds = [sequence[:maxLength] for sequence in tokenIds]

        if padding:
            longest = max((len(sequence) for sequence in tokenIds), default=0)
            attentionMask = [
                [1] * len(sequence) + [0] * (longest - len(sequence)) for sequence in tokenIds
            ]
            tokenIds = [
                sequence + [self._padId] * (longest - len(sequence)) for sequence in tokenIds
            ]
        else:
            attentionMask = [[1] * len(sequence) for sequence in tokenIds]

        return {"inputIds": tokenIds, "attentionMask": attentionMask}

    def decode(self, tokenIds: list[int], skipSpecialTokens: bool = True) -> str:
        """Decode token ids back into text."""
        return cast(
            "str",
            self._hfTokenizer.decode(
                tokenIds,
                skip_special_tokens=skipSpecialTokens,
            ),
        )

    def decodeBatch(
        self,
        tokenIdsList: list[list[int]],
        skipSpecialTokens: bool = True,
    ) -> list[str]:
        """Decode several sequences back into text."""
        return [
            self.decode(tokenIds, skipSpecialTokens=skipSpecialTokens) for tokenIds in tokenIdsList
        ]

    def tokenToId(self, token: str) -> int | None:
        """Return the id of a token, or None when unknown."""
        return self._vocab.get(token)

    def idToToken(self, tokenId: int) -> str | None:
        """Return the token for an id, or None when unknown."""
        return self._idToToken.get(tokenId)

    def getAllTokens(self) -> list[dict[str, int | str]]:
        """Return every (token, id) pair of the vocabulary, sorted by id."""
        return [
            {"token": token, "tokenId": tokenId}
            for token, tokenId in sorted(self._vocab.items(), key=lambda item: item[1])
        ]


@dataclass(frozen=True)
class EncodedCorpusStats:
    """Outcome of one full-corpus encoding run."""

    totalTokens: int
    totalDocuments: int
    shardCount: int
    avgTokensPerDoc: float
    languageDistribution: dict[str, int]
    durationSeconds: float = 0.0

    def toDict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "totalTokens": self.totalTokens,
            "totalDocuments": self.totalDocuments,
            "shardCount": self.shardCount,
            "avgTokensPerDoc": self.avgTokensPerDoc,
            "languageDistribution": dict(self.languageDistribution),
            "durationSeconds": self.durationSeconds,
        }


class TokenizerTrainRequest(BaseModel):
    """HTTP payload used to train a BPE tokenizer."""

    vocabSize: int = Field(default=32_000, ge=256, le=200_000)
    minFrequency: int = Field(default=2, ge=1)
    corpusSampleSize: int = Field(default=20_000, ge=1, le=1_000_000)
    languages: list[str] = Field(default_factory=lambda: ["fr"], min_length=1)
    showProgress: bool = False
    numThreads: int = Field(default=4, ge=1, le=64)

    def toConfig(self) -> TokenizerConfig:
        """Convert the validated request into a domain configuration."""
        return TokenizerConfig(
            vocabSize=self.vocabSize,
            minFrequency=self.minFrequency,
            showProgress=self.showProgress,
            numThreads=self.numThreads,
        )


class CorpusEncodeRequest(BaseModel):
    """HTTP payload used to encode the clean corpus into shards."""

    tokenizerPath: str | None = None
    shardSizeTokens: int = Field(default=100_000_000, ge=1_000)
    languages: list[str] | None = Field(default=None, min_length=1)


class TokenizerPreviewRequest(BaseModel):
    """HTTP payload used to tokenize a sample text."""

    text: str = Field(min_length=1, max_length=200_000)
