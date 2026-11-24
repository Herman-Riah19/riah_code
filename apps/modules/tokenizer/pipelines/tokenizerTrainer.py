# apps/modules/tokenizer/pipelines/tokenizerTrainer.py
"""Train a byte-level BPE tokenizer on clean corpus texts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Iterable

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, processors, trainers
from tokenizers.normalizers import NFKC, Sequence

from apps.modules.shared.kernel.exceptions import ValidationError

from ..models.tokenizerModel import TokenizerConfig, VocabInfo


class TokenizerTrainer:
    """Build, train and evaluate one BPE tokenizer."""

    def __init__(self, config: TokenizerConfig) -> None:
        self._config = config
        self._hfTokenizer = self._buildTokenizer()

    @property
    def hfTokenizer(self) -> Tokenizer:
        """Underlying Hugging Face tokenizer, ready to be saved."""
        return self._hfTokenizer

    def _buildTokenizer(self) -> Tokenizer:
        tokenizer = Tokenizer(models.BPE(unk_token="<|unk|>"))
        tokenizer.normalizer = Sequence([NFKC()])
        tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(
            add_prefix_space=self._config.addPrefixSpace
        )
        tokenizer.decoder = decoders.ByteLevel()
        tokenizer.post_processor = processors.ByteLevel(
            trim_offsets=self._config.trimWhitespace
        )
        return tokenizer

    def train(self, corpusIterator: Iterable[str]) -> VocabInfo:
        """Train on a stream of texts and return vocabulary metadata."""
        texts = [text for text in corpusIterator if text and text.strip()]
        if not texts:
            raise ValidationError(
                "Corpus vide: impossible d'entrainer le tokenizer",
            )

        trainer = trainers.BpeTrainer(
            vocab_size=self._config.vocabSize,
            min_frequency=self._config.minFrequency,
            special_tokens=list(self._config.specialTokens),
            show_progress=self._config.showProgress,
        )
        self._hfTokenizer.train_from_iterator(
            texts,
            trainer=trainer,
            length=len(texts),
        )
        return self._computeVocabInfo(texts)

    def _computeVocabInfo(self, texts: list[str]) -> VocabInfo:
        vocab = self._hfTokenizer.get_vocab()
        specialTokenIds = {
            token: vocab[token]
            for token in self._config.specialTokens
            if token in vocab
        }

        encodedSequences = self._encodeAll(texts)
        totalChars = sum(len(text) for text in texts)
        totalTokens = sum(len(sequence) for sequence in encodedSequences)
        compressionRatio = totalChars / totalTokens if totalTokens else 0.0

        unkTokenId = specialTokenIds.get("<|unk|>")
        oovCount = sum(
            1
            for sequence in encodedSequences
            for tokenId in sequence
            if tokenId == unkTokenId
        )
        oovRate = oovCount / totalTokens if totalTokens else 0.0

        return VocabInfo(
            vocabSize=len(vocab),
            specialTokenIds=specialTokenIds,
            compressionRatio=compressionRatio,
            oovRate=oovRate,
            trainedAt=datetime.now(timezone.utc),
            configHash=self._config.configHash(),
        )

    def _encodeAll(self, texts: list[str]) -> list[list[int]]:
        with ThreadPoolExecutor(max_workers=self._config.numThreads) as executor:
            return list(executor.map(self._encodeOne, texts))

    def _encodeOne(self, text: str) -> list[int]:
        return list(self._hfTokenizer.encode(text).ids)
