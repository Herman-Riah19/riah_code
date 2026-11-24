# tests/unit/test_tokenizer/conftest.py
"""Shared fixtures for tokenizer unit tests."""

from pathlib import Path

import pytest

from apps.modules.tokenizer.models.tokenizerModel import (
    BPETokenizer,
    TokenizerConfig,
    VocabInfo,
)
from apps.modules.tokenizer.pipelines.tokenizerTrainer import TokenizerTrainer
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository

from tinyCorpus import TINY_CORPUS_TEXTS


@pytest.fixture(scope="session")
def tinyTokenizerDir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Train one small tokenizer and persist it once for the whole session."""
    directory = tmp_path_factory.mktemp("tiny_tokenizer")
    repository = TokenizerRepository(directory)
    trainer = TokenizerTrainer(
        TokenizerConfig(
            vocabSize=512,
            minFrequency=1,
            showProgress=False,
            numThreads=2,
        )
    )
    vocabInfo = trainer.train(TINY_CORPUS_TEXTS)
    repository.save(trainer.hfTokenizer, vocabInfo)
    return directory


@pytest.fixture(scope="session")
def tinyTokenizer(tinyTokenizerDir: Path) -> tuple[BPETokenizer, VocabInfo]:
    """Load the persisted tiny tokenizer and its metadata."""
    return TokenizerRepository(tinyTokenizerDir).load()
