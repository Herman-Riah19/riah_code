# tests/unit/test_tokenizer/test_tokenizerModel.py
"""Tests for tokenizer domain models and the BPE runtime wrapper."""

from datetime import datetime, timezone

from apps.modules.tokenizer.models.tokenizerModel import (
    BPETokenizer,
    TokenizerConfig,
    VocabInfo,
)

from tinyCorpus import TINY_CORPUS_TEXTS


class TestTokenizerConfig:
    """Configuration hash must be stable and sensitive to changes."""

    def test_config_hash_is_stable(self) -> None:
        assert TokenizerConfig().configHash() == TokenizerConfig().configHash()

    def test_config_hash_changes_with_vocab_size(self) -> None:
        assert TokenizerConfig(vocabSize=1000).configHash() != TokenizerConfig(
            vocabSize=2000
        ).configHash()

    def test_config_hash_is_short_hex(self) -> None:
        configHash = TokenizerConfig().configHash()
        assert len(configHash) == 16
        assert int(configHash, 16) >= 0


class TestVocabInfo:
    """Vocabulary metadata must survive a JSON round-trip."""

    def test_json_round_trip(self) -> None:
        original = VocabInfo(
            vocabSize=512,
            specialTokenIds={"<|endoftext|>": 0, "<|pad|>": 1},
            compressionRatio=3.75,
            oovRate=0.0,
            trainedAt=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            configHash="0123456789abcdef",
        )

        restored = VocabInfo.fromJson(original.toJson())

        assert restored == original

    def test_dict_contains_camel_case_keys(self) -> None:
        payload = VocabInfo(
            vocabSize=10,
            specialTokenIds={},
            compressionRatio=1.0,
            oovRate=0.0,
            trainedAt=datetime.now(timezone.utc),
            configHash="abc",
        ).toDict()

        assert set(payload) == {
            "vocabSize",
            "specialTokenIds",
            "compressionRatio",
            "oovRate",
            "trainedAt",
            "configHash",
        }


class TestBPETokenizer:
    """Runtime wrapper - encode, decode, batching and lookups."""

    def test_special_token_ids_are_exposed(self, tinyTokenizer) -> None:
        tokenizer, vocabInfo = tinyTokenizer

        assert tokenizer.vocabSize == vocabInfo.vocabSize
        assert tokenizer.eosTokenId == vocabInfo.specialTokenIds["<|endoftext|>"]
        assert tokenizer.padTokenId == vocabInfo.specialTokenIds["<|pad|>"]
        assert tokenizer.unkTokenId == vocabInfo.specialTokenIds["<|unk|>"]

    def test_encode_appends_eos(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        text = TINY_CORPUS_TEXTS[0]

        withEos = tokenizer.encode(text)
        withoutEos = tokenizer.encode(text, addSpecialTokens=False)

        assert withEos[-1] == tokenizer.eosTokenId
        assert withEos[:-1] == withoutEos

    def test_encode_decode_round_trip(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        text = TINY_CORPUS_TEXTS[2]

        decoded = tokenizer.decode(tokenizer.encode(text))

        assert decoded.strip() == text

    def test_decode_can_keep_special_tokens(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        tokenIds = tokenizer.encode("bonjour")

        assert "<|endoftext|>" in tokenizer.decode(
            tokenIds,
            skipSpecialTokens=False,
        )

    def test_encode_batch_pads_sequences(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        texts = [TINY_CORPUS_TEXTS[0], TINY_CORPUS_TEXTS[1]]

        batch = tokenizer.encodeBatch(texts, padding=True)

        lengths = {len(sequence) for sequence in batch["inputIds"]}
        assert len(lengths) == 1
        assert all(
            len(sequence) == len(mask)
            for sequence, mask in zip(batch["inputIds"], batch["attentionMask"])
        )
        assert all(
            tokenId == tokenizer.padTokenId
            for tokenId, flag in zip(batch["inputIds"][0], batch["attentionMask"][0])
            if flag == 0
        )

    def test_encode_batch_without_padding(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        texts = [TINY_CORPUS_TEXTS[0], TINY_CORPUS_TEXTS[1]]

        batch = tokenizer.encodeBatch(texts, padding=False)

        assert all(
            len(sequence) == len(mask)
            for sequence, mask in zip(batch["inputIds"], batch["attentionMask"])
        )
        assert all(flag == 1 for mask in batch["attentionMask"] for flag in mask)

    def test_encode_batch_truncates(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer

        batch = tokenizer.encodeBatch(
            [TINY_CORPUS_TEXTS[0]],
            padding=False,
            maxLength=5,
        )

        assert len(batch["inputIds"][0]) == 5

    def test_token_lookups(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer

        assert tokenizer.tokenToId("<|endoftext|>") == tokenizer.eosTokenId
        assert tokenizer.idToToken(tokenizer.eosTokenId) == "<|endoftext|>"
        assert tokenizer.tokenToId("token-inexistant") is None
        assert tokenizer.idToToken(10**9) is None

    def test_decode_batch(self, tinyTokenizer) -> None:
        tokenizer, _ = tinyTokenizer
        texts = list(TINY_CORPUS_TEXTS[:2])

        decoded = tokenizer.decodeBatch([tokenizer.encode(text) for text in texts])

        assert [text.strip() for text in decoded] == texts


def test_bpe_tokenizer_requires_special_tokens(tmp_path) -> None:
    """Loading a tokenizer without the required special tokens must fail."""
    from tokenizers import Tokenizer, models

    rawPath = tmp_path / "tokenizer.json"
    rawTokenizer = Tokenizer(models.BPE())
    rawTokenizer.save(str(rawPath))

    try:
        BPETokenizer(rawPath)
    except ValueError as error:
        assert "<|endoftext|>" in str(error)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("BPETokenizer aurait du lever ValueError")
