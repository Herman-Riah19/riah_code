# tests/unit/test_model/test_inferenceService.py
"""Tests for the inference service - caching, generation and model cards."""

from __future__ import annotations

from pathlib import Path

import pytest
from fakes import (
    FakeTokenizer,
    FakeTokenizerRepository,
    SilentTokenizer,
    cpuModelFactory,
    makeCheckpoint,
)
from tinyModel import tinyGenerationOptions, tinyModelConfig

from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.model.services.inferenceService import InferenceService
from apps.modules.shared.kernel.exceptions import (
    CheckpointNotFoundError,
    NoModelAvailableError,
    TokenizerNotFoundError,
    ValidationError,
)


class InferenceFixture:
    """Bundle the service, its repositories and one persisted checkpoint."""

    def __init__(
        self,
        tmp_path: Path,
        *,
        capacity: int = 2,
        tokenizer: FakeTokenizer | None = None,
        failTokenizer: bool = False,
    ) -> None:
        self.baseDir = tmp_path
        self.checkpointRepo = CheckpointRepository(tmp_path / "checkpoints")
        self.tokenizerRepo = FakeTokenizerRepository(
            fail=failTokenizer,
            tokenizer=tokenizer,
        )
        self.service = InferenceService(
            tokenizerRepo=self.tokenizerRepo,  # type: ignore[arg-type]
            checkpointRepo=self.checkpointRepo,
            modelFactory=cpuModelFactory,
            cacheCapacity=capacity,
        )
        self.checkpoint = makeCheckpoint(tmp_path, self.checkpointRepo, "ckpt-a")


@pytest.fixture
def fixture(tmp_path: Path) -> InferenceFixture:
    """Default inference fixture with one (non-best) checkpoint."""
    return InferenceFixture(tmp_path)


def makeService(
    tmp_path: Path,
    *,
    capacity: int = 2,
    tokenizer: FakeTokenizer | None = None,
) -> tuple[InferenceService, CheckpointRepository]:
    """Build a service over an isolated checkpoint repository."""
    repository = CheckpointRepository(tmp_path / "checkpoints")
    service = InferenceService(
        tokenizerRepo=FakeTokenizerRepository(tokenizer=tokenizer),  # type: ignore[arg-type]
        checkpointRepo=repository,
        modelFactory=cpuModelFactory,
        cacheCapacity=capacity,
    )
    return service, repository


class TestModelResolution:
    """Checkpoint resolution and lazy loading."""

    def test_resolve_prefers_the_best_checkpoint(self, fixture: InferenceFixture) -> None:
        makeCheckpoint(
            fixture.baseDir,
            fixture.checkpointRepo,
            "ckpt-best",
            step=9,
            isBest=True,
        )

        assert fixture.service.resolveCheckpoint(None).id == "ckpt-best"

    def test_resolve_prefers_the_most_advanced_best_checkpoint(
        self, fixture: InferenceFixture
    ) -> None:
        makeCheckpoint(
            fixture.baseDir,
            fixture.checkpointRepo,
            "ckpt-best-old",
            step=4,
            isBest=True,
        )
        makeCheckpoint(
            fixture.baseDir,
            fixture.checkpointRepo,
            "ckpt-best-new",
            step=11,
            isBest=True,
        )

        assert fixture.service.resolveCheckpoint(None).id == "ckpt-best-new"

    def test_resolve_falls_back_to_the_latest(self, fixture: InferenceFixture) -> None:
        makeCheckpoint(fixture.baseDir, fixture.checkpointRepo, "ckpt-late", step=12)

        assert fixture.service.resolveCheckpoint(None).id == "ckpt-late"

    def test_resolve_explicit_id(self, fixture: InferenceFixture) -> None:
        assert fixture.service.resolveCheckpoint("ckpt-a").id == "ckpt-a"

    def test_resolve_empty_id_uses_the_default(self, fixture: InferenceFixture) -> None:
        assert fixture.service.resolveCheckpoint("").id == "ckpt-a"

    def test_unknown_id_raises(self, fixture: InferenceFixture) -> None:
        with pytest.raises(CheckpointNotFoundError):
            fixture.service.resolveCheckpoint("missing")

    def test_no_checkpoint_raises(self, tmp_path: Path) -> None:
        service, _ = makeService(tmp_path)

        with pytest.raises(NoModelAvailableError):
            service.loadModel()

    def test_load_caches_the_runner(self, fixture: InferenceFixture) -> None:
        first = fixture.service.loadModel("ckpt-a")
        second = fixture.service.loadModel("ckpt-a")

        assert first is second
        assert fixture.service.cacheSize == 1

    def test_load_without_id_uses_the_default_checkpoint(self, fixture: InferenceFixture) -> None:
        runner = fixture.service.loadModel()

        assert runner is fixture.service.loadModel(fixture.checkpoint.id)

    def test_lru_evicts_the_least_recently_used_model(self, tmp_path: Path) -> None:
        service, repository = makeService(tmp_path, capacity=2)
        makeCheckpoint(tmp_path, repository, "ckpt-a", step=2)
        makeCheckpoint(tmp_path, repository, "ckpt-b", step=3)
        makeCheckpoint(tmp_path, repository, "ckpt-c", step=4)

        service.loadModel("ckpt-a")
        service.loadModel("ckpt-b")
        service.loadModel("ckpt-a")  # Refresh "ckpt-a": "ckpt-b" is now the oldest.
        service.loadModel("ckpt-c")

        assert service.cacheSize == 2
        assert service.unload("ckpt-b") is False
        assert service.unload("ckpt-a") is True
        assert service.unload("ckpt-c") is True

    def test_unload_unknown_model_returns_false(self, fixture: InferenceFixture) -> None:
        assert fixture.service.unload("unknown") is False

    def test_clear_cache(self, fixture: InferenceFixture) -> None:
        fixture.service.loadModel("ckpt-a")
        fixture.service.clearCache()

        assert fixture.service.cacheSize == 0


class TestGeneration:
    """Non-streaming and streaming generation."""

    def test_generate_returns_completion_and_text(self, fixture: InferenceFixture) -> None:
        output = fixture.service.generate(
            "abc",
            tinyGenerationOptions(maxTokens=3),
            checkpointId="ckpt-a",
        )

        assert output.completion == "aaa"
        assert output.generatedTokens == 3
        assert output.text.endswith("aaa")
        assert output.prompt == "abc"
        assert output.checkpointId == "ckpt-a"

    def test_generate_dict_shape(self, fixture: InferenceFixture) -> None:
        output = fixture.service.generate(
            "abc",
            tinyGenerationOptions(maxTokens=1),
        )

        assert set(output.toDict()) == {
            "prompt",
            "completion",
            "text",
            "generatedTokens",
            "checkpointId",
        }

    def test_generation_stops_on_eos(self, tmp_path: Path) -> None:
        service, repository = makeService(tmp_path)
        makeCheckpoint(tmp_path, repository, "eos-zero", eosTokenId=0)

        output = service.generate(
            "abc",
            tinyGenerationOptions(maxTokens=4),
            checkpointId="eos-zero",
        )

        assert output.completion == "a"
        assert output.generatedTokens == 1

    def test_generate_respects_max_tokens(self, fixture: InferenceFixture) -> None:
        output = fixture.service.generate(
            "abc",
            tinyGenerationOptions(maxTokens=2),
        )

        assert output.generatedTokens == 2

    def test_generate_is_deterministic_with_a_seed(self, fixture: InferenceFixture) -> None:
        options = tinyGenerationOptions(
            maxTokens=4,
            temperature=0.7,
            topK=None,
            repetitionPenalty=1.0,
            seed=1234,
        )

        first = fixture.service.generate("abc", options)
        second = fixture.service.generate("abc", options)

        assert first.completion == second.completion

    def test_stop_sequences_are_resolved_through_the_tokenizer(self, tmp_path: Path) -> None:
        # Every encoded piece maps to token 0, which is also what the model
        # produces: the stop sequence must cut generation immediately.
        tokenizer = FakeTokenizer(encodeTo=0)
        service, repository = makeService(tmp_path, tokenizer=tokenizer)
        makeCheckpoint(tmp_path, repository, "ckpt-a")

        output = service.generate(
            "abc",
            tinyGenerationOptions(maxTokens=5, stopSequences=["!"]),
            checkpointId="ckpt-a",
        )

        assert output.generatedTokens == 1

    def test_stream_generate_respects_stop_sequences(self, tmp_path: Path) -> None:
        tokenizer = FakeTokenizer(encodeTo=0)
        service, repository = makeService(tmp_path, tokenizer=tokenizer)
        makeCheckpoint(tmp_path, repository, "ckpt-a")

        deltas = list(
            service.streamGenerate(
                "abc",
                tinyGenerationOptions(maxTokens=5, stopSequences=["!"]),
                checkpointId="ckpt-a",
            )
        )

        assert deltas == ["a"]

    def test_empty_prompt_is_rejected(self, fixture: InferenceFixture) -> None:
        with pytest.raises(ValidationError, match="vide"):
            fixture.service.generate("", tinyGenerationOptions())

    def test_whitespace_prompt_is_rejected(self, fixture: InferenceFixture) -> None:
        with pytest.raises(ValidationError, match="vide"):
            fixture.service.generate("   ", tinyGenerationOptions())

    def test_prompt_without_tokens_is_rejected(self, tmp_path: Path) -> None:
        service, repository = makeService(tmp_path, tokenizer=SilentTokenizer())
        makeCheckpoint(tmp_path, repository, "ckpt-a")

        with pytest.raises(ValidationError, match="aucun token"):
            service.generate("abc", tinyGenerationOptions(), checkpointId="ckpt-a")

    def test_missing_tokenizer_raises(self, tmp_path: Path) -> None:
        fixture = InferenceFixture(tmp_path, failTokenizer=True)

        with pytest.raises(TokenizerNotFoundError):
            fixture.service.generate("abc", tinyGenerationOptions())

    def test_long_prompt_is_truncated_to_the_context(self, fixture: InferenceFixture) -> None:
        output = fixture.service.generate(
            "a" * 200,
            tinyGenerationOptions(maxTokens=2),
        )

        # The prompt keeps its last `maxSeqLen` tokens, so generation stops
        # as soon as the KV cache reaches the context window.
        maxSeqLen = tinyModelConfig().maxSeqLen
        assert output.generatedTokens >= 1
        assert len(output.text) == maxSeqLen + output.generatedTokens

    def test_stream_generate_yields_deltas(self, fixture: InferenceFixture) -> None:
        deltas = list(
            fixture.service.streamGenerate(
                "abc",
                tinyGenerationOptions(maxTokens=3),
                checkpointId="ckpt-a",
            )
        )

        assert deltas == ["a", "a", "a"]

    def test_stream_generate_stops_on_eos(self, tmp_path: Path) -> None:
        service, repository = makeService(tmp_path)
        makeCheckpoint(tmp_path, repository, "eos-zero", eosTokenId=0)

        deltas = list(
            service.streamGenerate(
                "abc",
                tinyGenerationOptions(maxTokens=3),
                checkpointId="eos-zero",
            )
        )

        assert deltas == ["a"]


class TestModelCards:
    """Model listing used by the inference dashboard."""

    def test_list_models_returns_cards(self, fixture: InferenceFixture) -> None:
        cards = fixture.service.listModels()

        assert len(cards) == 1
        card = cards[0]
        assert card["id"] == "ckpt-a"
        assert card["modelName"] == "tiny"
        assert card["parameters"] > 0
        assert card["valLoss"] == 0.9
        assert card["isBest"] is False
        architecture = card["architecture"]
        assert isinstance(architecture, dict)
        assert architecture["vocabSize"] == 64
        assert architecture["maxSeqLen"] == 32
        assert architecture["dtype"] == "fp32"

    def test_list_models_respects_the_limit(self, fixture: InferenceFixture) -> None:
        makeCheckpoint(fixture.baseDir, fixture.checkpointRepo, "ckpt-b", step=6)

        assert len(fixture.service.listModels(limit=1)) == 1
        assert fixture.service.listModels(limit=0) == []

    def test_get_model_info(self, fixture: InferenceFixture) -> None:
        card = fixture.service.getModelInfo("ckpt-a")

        assert card["id"] == "ckpt-a"
        assert card["step"] == 5
        assert card["modelName"] == "tiny"

    def test_get_unknown_model_info_raises(self, fixture: InferenceFixture) -> None:
        with pytest.raises(CheckpointNotFoundError):
            fixture.service.getModelInfo("missing")
