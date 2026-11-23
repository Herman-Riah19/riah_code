# apps/modules/corpus/pipelines/qualityFilter.py
"""Heuristic quality scoring and filtering for clean documents."""
from __future__ import annotations

import re
from collections import Counter

from ..models.corpusModel import CleanDocument, QualityFilterConfig

MIN_QUALITY_SCORE = 0.5
WORD_PATTERN = re.compile(r"\w+", re.UNICODE)
SYMBOL_PATTERN = re.compile(r"[^\w\s]", re.UNICODE)


class QualityFilter:
    """Assign a 0..1 quality score and decide whether a document is kept."""

    def __init__(self, config: QualityFilterConfig | None = None) -> None:
        self._config = config or QualityFilterConfig()

    def score(self, text: str, language: str) -> float:
        """Return a heuristic quality score in the [0, 1] range."""
        if not text:
            return 0.0

        scoreValue = 1.0
        charLength = len(text)
        if charLength < self._config.minCharLength or charLength > self._config.maxCharLength:
            scoreValue -= 0.4

        words = WORD_PATTERN.findall(text)
        if len(words) < self._config.minWordCount:
            scoreValue -= 0.3

        symbolRatio = len(SYMBOL_PATTERN.findall(text)) / charLength
        if symbolRatio > self._config.maxSymbolRatio:
            scoreValue -= 0.3

        if self._repetitionRatio(words) > self._config.maxRepetitionRatio:
            scoreValue -= 0.2

        if language not in self._config.targetLanguages:
            scoreValue -= 0.5

        return max(0.0, min(1.0, scoreValue))

    def accepts(self, document: CleanDocument) -> bool:
        """Return True when a clean document passes every hard threshold."""
        if document.language not in self._config.targetLanguages:
            return False
        if not self._config.minCharLength <= len(document.text) <= self._config.maxCharLength:
            return False
        if document.tokenCount < self._config.minWordCount:
            return False
        return document.qualityScore >= MIN_QUALITY_SCORE

    def _repetitionRatio(self, words: list[str]) -> float:
        if not words:
            return 0.0
        mostCommon = Counter(words).most_common(1)
        if not mostCommon:
            return 0.0
        return mostCommon[0][1] / len(words)
