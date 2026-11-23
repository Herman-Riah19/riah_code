# apps/modules/corpus/pipelines/textNormalizer.py
"""Unicode, whitespace and control character normalization."""
from __future__ import annotations

import re
import unicodedata

from ..models.corpusModel import TextNormalizerConfig

CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HORIZONTAL_SPACES_PATTERN = re.compile(r"[ \t\f\v]+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")
MOJIBAKE_MARKERS = ("Ã", "Â", "â€")


class TextNormalizer:
    """Normalize text so every document uses the same canonical form."""

    def __init__(self, config: TextNormalizerConfig | None = None) -> None:
        self._config = config or TextNormalizerConfig()

    def normalize(self, text: str) -> str:
        """Apply the configured normalization pipeline to the given text."""
        if not text:
            return ""
        normalized = unicodedata.normalize(self._config.unicodeForm, text)
        if self._config.fixMojibake:
            normalized = self._fixMojibake(normalized)
        if self._config.removeControlChars:
            normalized = CONTROL_CHARS_PATTERN.sub("", normalized)
        if self._config.collapseWhitespace:
            normalized = HORIZONTAL_SPACES_PATTERN.sub(" ", normalized)
            normalized = MULTI_NEWLINE_PATTERN.sub("\n\n", normalized)

        cleanedLines = [line.strip() for line in normalized.splitlines() if line.strip()]
        if len(cleanedLines) > 1:
            cleanedLines = [
                line for line in cleanedLines if len(line) >= self._config.minLineLength
            ]
        return "\n".join(cleanedLines)

    def _fixMojibake(self, text: str) -> str:
        if not any(marker in text for marker in MOJIBAKE_MARKERS):
            return text
        try:
            repaired = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text
        return repaired
