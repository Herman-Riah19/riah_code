# tests/unit/test_tokenizer/test_tokenizerRepository.py
"""Tests for the tokenizer repository - local artifacts persistence."""

from pathlib import Path

import pytest
from tokenizers import Tokenizer as HFTokenizer

from apps.modules.shared.kernel.exceptions import TokenizerNotFoundError
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository


class TestTokenizerRepository:
    """Save, load and detect tokenizer artifacts."""

    def test_exists_is_false_on_empty_directory(self, tmp_path: Path) -> None:
        repository = TokenizerRepository(tmp_path / "tokenizer")

        assert repository.exists() is False
        assert repository.tokenizerPath.name == "tokenizer.json"

    def test_load_without_artifacts_raises(self, tmp_path: Path) -> None:
        repository = TokenizerRepository(tmp_path / "tokenizer")

        with pytest.raises(TokenizerNotFoundError):
            repository.load()

    def test_save_then_load(self, tmp_path: Path, tinyTokenizerDir: Path) -> None:
        sourceRepository = TokenizerRepository(tinyTokenizerDir)
        _, vocabInfo = sourceRepository.load()
        hfTokenizer = HFTokenizer.from_file(str(sourceRepository.tokenizerPath))

        repository = TokenizerRepository(tmp_path / "tokenizer")
        savedPath = repository.save(hfTokenizer, vocabInfo)

        assert savedPath.is_file()
        assert repository.exists() is True
        assert not list(repository.baseDir.glob("*.tmp"))

        tokenizer, loadedInfo = repository.load()
        assert tokenizer.vocabSize == vocabInfo.vocabSize
        assert loadedInfo == vocabInfo

    def test_save_overwrites_previous_artifacts(
        self,
        tmp_path: Path,
        tinyTokenizerDir: Path,
    ) -> None:
        sourceRepository = TokenizerRepository(tinyTokenizerDir)
        _, vocabInfo = sourceRepository.load()
        hfTokenizer = HFTokenizer.from_file(str(sourceRepository.tokenizerPath))
        repository = TokenizerRepository(tmp_path / "tokenizer")

        repository.save(hfTokenizer, vocabInfo)
        repository.save(hfTokenizer, vocabInfo)

        assert repository.exists() is True
        assert len(list(repository.baseDir.iterdir())) == 2
