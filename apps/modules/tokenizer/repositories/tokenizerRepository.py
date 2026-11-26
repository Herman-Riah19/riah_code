# apps/modules/tokenizer/repositories/tokenizerRepository.py
"""Tokenizer repository - local `tokenizer.json` and `vocab_info.json` files."""

from __future__ import annotations

from pathlib import Path

from tokenizers import Tokenizer as HFTokenizer

from apps.modules.shared.kernel.exceptions import TokenizerNotFoundError

from ..models.tokenizerModel import BPETokenizer, VocabInfo

TOKENIZER_FILE_NAME = "tokenizer.json"
VOCAB_INFO_FILE_NAME = "vocab_info.json"


class TokenizerRepository:
    """Persist and load a trained tokenizer from the local data directory."""

    def __init__(self, baseDir: Path) -> None:
        self._baseDir = baseDir
        self._tokenizerPath = baseDir / TOKENIZER_FILE_NAME
        self._vocabInfoPath = baseDir / VOCAB_INFO_FILE_NAME

    @property
    def baseDir(self) -> Path:
        """Directory holding the tokenizer artifacts."""
        return self._baseDir

    @property
    def tokenizerPath(self) -> Path:
        """Path of the `tokenizer.json` file."""
        return self._tokenizerPath

    def save(self, hfTokenizer: HFTokenizer, vocabInfo: VocabInfo) -> Path:
        """Atomically write the tokenizer and its metadata, then return the path."""
        self._baseDir.mkdir(parents=True, exist_ok=True)
        temporaryPath = self._tokenizerPath.with_suffix(".json.tmp")
        hfTokenizer.save(str(temporaryPath))
        temporaryPath.replace(self._tokenizerPath)
        self._vocabInfoPath.write_text(vocabInfo.toJson(), encoding="utf-8")
        return self._tokenizerPath

    def load(self) -> tuple[BPETokenizer, VocabInfo]:
        """Load the runtime tokenizer and its metadata."""
        if not self.exists():
            raise TokenizerNotFoundError(
                "Tokenizer introuvable",
                details={"path": str(self._tokenizerPath)},
            )
        tokenizer = BPETokenizer(self._tokenizerPath)
        vocabInfo = VocabInfo.fromJson(self._vocabInfoPath.read_text(encoding="utf-8"))
        return tokenizer, vocabInfo

    def exists(self) -> bool:
        """Return True when both tokenizer artifacts are present."""
        return self._tokenizerPath.is_file() and self._vocabInfoPath.is_file()
