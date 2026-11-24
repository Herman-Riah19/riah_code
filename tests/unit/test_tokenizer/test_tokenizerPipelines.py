# tests/unit/test_tokenizer/test_pipelines.py
"""Tests for the tokenizer trainer and the corpus encoder."""

import json
from array import array
from datetime import datetime, timezone
from pathlib import Path

import pytest

from apps.modules.corpus.models.corpusModel import CleanDocument
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.kernel.exceptions import ValidationError
from apps.modules.tokenizer.models.tokenizerModel import TokenizerConfig
from apps.modules.tokenizer.pipelines.corpusEncoder import CorpusEncoder
from apps.modules.tokenizer.pipelines.tokenizerTrainer import TokenizerTrainer

from tinyCorpus import TINY_CORPUS_TEXTS


def makeCleanDocument(
    documentId: str,
    text: str,
    language: str = "fr",
) -> CleanDocument:
    """Build a minimal clean document for encoding tests."""
    return CleanDocument(
        id=documentId,
        source="wikipedia",
        language=language,
        text=text,
        qualityScore=0.9,
        tokenCount=len(text.split()),
        cleanedAt=datetime.now(timezone.utc),
    )


class TestTokenizerTrainer:
    """BPE training on a small corpus."""

    def test_empty_corpus_raises(self) -> None:
        trainer = TokenizerTrainer(TokenizerConfig(vocabSize=256, showProgress=False))

        with pytest.raises(ValidationError):
            trainer.train(iter(["", "   "]))

    def test_train_reports_vocabulary_metadata(self) -> None:
        config = TokenizerConfig(
            vocabSize=512,
            minFrequency=1,
            showProgress=False,
            numThreads=2,
        )
        trainer = TokenizerTrainer(config)

        vocabInfo = trainer.train(iter(TINY_CORPUS_TEXTS))

        assert 4 < vocabInfo.vocabSize <= 512
        assert set(vocabInfo.specialTokenIds) == {
            "<|endoftext|>",
            "<|pad|>",
            "<|unk|>",
            "<|mask|>",
        }
        assert vocabInfo.compressionRatio > 1.0
        assert vocabInfo.oovRate == 0.0
        assert vocabInfo.configHash == config.configHash()

    def test_training_is_reproducible(self) -> None:
        config = TokenizerConfig(
            vocabSize=512,
            minFrequency=1,
            showProgress=False,
            numThreads=2,
        )

        firstInfo = TokenizerTrainer(config).train(iter(TINY_CORPUS_TEXTS))
        secondInfo = TokenizerTrainer(config).train(iter(TINY_CORPUS_TEXTS))

        assert firstInfo.vocabSize == secondInfo.vocabSize
        assert firstInfo.compressionRatio == secondInfo.compressionRatio
        assert firstInfo.configHash == secondInfo.configHash

    def test_tokenizer_json_is_byte_identical(self, tmp_path: Path) -> None:
        config = TokenizerConfig(
            vocabSize=512,
            minFrequency=1,
            showProgress=False,
            numThreads=2,
        )
        firstTrainer = TokenizerTrainer(config)
        firstTrainer.train(iter(TINY_CORPUS_TEXTS))
        secondTrainer = TokenizerTrainer(config)
        secondTrainer.train(iter(TINY_CORPUS_TEXTS))

        firstPath = tmp_path / "first.json"
        secondPath = tmp_path / "second.json"
        firstTrainer.hfTokenizer.save(str(firstPath))
        secondTrainer.hfTokenizer.save(str(secondPath))

        assert firstPath.read_bytes() == secondPath.read_bytes()


class TestCorpusEncoder:
    """Shard writing and index updates."""

    def test_encode_corpus_writes_shards(
        self,
        tmp_path: Path,
        tinyTokenizer,
    ) -> None:
        tokenizer, _ = tinyTokenizer
        corpusRepo = CorpusRepository(tmp_path / "corpus")
        documents = [
            makeCleanDocument("doc-1", "Le petit chat dort sur le tapis."),
            makeCleanDocument("doc-2", "Les enfants jouent dans le jardin."),
            makeCleanDocument("doc-3", "The model predicts the next token.", "en"),
        ]
        corpusRepo.saveClean(documents)

        encoder = CorpusEncoder(
            tokenizer=tokenizer,
            corpusRepo=corpusRepo,
            shardSizeTokens=15,
        )
        stats = encoder.encodeCorpus(corpusRepo.loadClean())

        assert stats.totalDocuments == 3
        assert stats.totalTokens > 0
        assert stats.shardCount >= 2
        assert stats.avgTokensPerDoc > 0
        assert stats.languageDistribution == {"fr": 2, "en": 1}

        shards = corpusRepo.getShardsForTraining()
        assert len(shards) == stats.shardCount
        assert sum(shard.tokenCount for shard in shards) == stats.totalTokens
        assert all(shard.filePath.is_file() for shard in shards)
        assert all(shard.indexPath.is_file() for shard in shards)

    def test_first_shard_round_trip(
        self,
        tmp_path: Path,
        tinyTokenizer,
    ) -> None:
        tokenizer, _ = tinyTokenizer
        corpusRepo = CorpusRepository(tmp_path / "corpus")
        text = "Le petit chat dort sur le tapis."
        corpusRepo.saveClean([makeCleanDocument("doc-1", text)])
        encoder = CorpusEncoder(
            tokenizer=tokenizer,
            corpusRepo=corpusRepo,
            shardSizeTokens=100,
        )

        encoder.encodeCorpus(corpusRepo.loadClean())

        shard = corpusRepo.getShardsForTraining()[0]
        tokenIds = array("H")
        tokenIds.frombytes(shard.filePath.read_bytes())
        firstEntry = json.loads(
            shard.indexPath.read_text(encoding="utf-8").splitlines()[0]
        )
        offset = int(firstEntry["offset"])
        length = int(firstEntry["length"])

        decoded = tokenizer.decode(list(tokenIds[offset : offset + length]))

        assert decoded.strip() == text
        assert length == len(tokenizer.encode(text))

    def test_encode_empty_corpus(self, tmp_path: Path, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        corpusRepo = CorpusRepository(tmp_path / "corpus")
        encoder = CorpusEncoder(tokenizer=tokenizer, corpusRepo=corpusRepo)

        stats = encoder.encodeCorpus(iter([]))

        assert stats.totalDocuments == 0
        assert stats.totalTokens == 0
        assert stats.shardCount == 0
        assert stats.avgTokensPerDoc == 0.0
        assert corpusRepo.getShardsForTraining() == []
