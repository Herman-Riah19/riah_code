# tests/unit/test_model/test_sampler.py
"""Tests for the token sampler."""

from __future__ import annotations

import pytest
import torch

from apps.modules.model.ml.sampler import Sampler


class TestSamplerValidation:
    """Constructor guards."""

    def test_rejects_negative_temperature(self) -> None:
        with pytest.raises(ValueError, match="temperature"):
            Sampler(temperature=-0.1)

    def test_rejects_invalid_top_p(self) -> None:
        with pytest.raises(ValueError, match="topP"):
            Sampler(topP=0.0)

    def test_rejects_invalid_repetition_penalty(self) -> None:
        with pytest.raises(ValueError, match="repetitionPenalty"):
            Sampler(repetitionPenalty=0.0)

    def test_rejects_negative_top_k(self) -> None:
        with pytest.raises(ValueError, match="topK"):
            Sampler(topK=-1)


class TestSamplerStrategies:
    """Greedy, top-k, top-p and repetition penalty behaviour."""

    def test_zero_temperature_is_greedy(self) -> None:
        logits = torch.tensor([[0.1, 3.0, 0.2, -1.0]])
        token = Sampler(temperature=0.0).sample(logits)
        assert token.item() == 1

    def test_top_k_one_is_greedy(self) -> None:
        logits = torch.tensor([[0.5, 0.1, 2.5, 0.0]])
        token = Sampler(temperature=1.0, topK=1).sample(logits)
        assert token.item() == 2

    def test_top_p_keeps_only_dominant_token(self) -> None:
        logits = torch.tensor([[10.0, 0.0, 0.0, 0.0]])
        sampler = Sampler(temperature=1.0, topK=None, topP=0.01)
        samples = {sampler.sample(logits).item() for _ in range(20)}
        assert samples == {0}

    def test_repetition_penalty_demotes_repeated_token(self) -> None:
        logits = torch.tensor([[0.0, 5.0, 0.0]])
        sampler = Sampler(temperature=0.0, repetitionPenalty=10.0)
        token = sampler.sample(logits, generatedTokens=[1])
        assert token.item() == 0

    def test_repetition_penalty_boosts_negative_logits(self) -> None:
        logits = torch.tensor([[0.0, -5.0, 0.0]])
        sampler = Sampler(temperature=0.0, repetitionPenalty=10.0)
        # -5 * 10 = -50, so the repeated token stays the worst option.
        assert sampler.sample(logits, generatedTokens=[1]).item() == 0

    def test_seeded_sampling_is_deterministic(self) -> None:
        logits = torch.randn(1, 32)
        first = Sampler(temperature=1.0, generator=self._generator(7)).sample(logits)
        second = Sampler(temperature=1.0, generator=self._generator(7)).sample(logits)
        assert first.item() == second.item()

    def test_sampled_token_is_in_vocabulary(self) -> None:
        logits = torch.randn(2, 16)
        tokens = Sampler(temperature=1.0).sample(logits)
        assert tokens.shape == (2, 1)
        assert bool(((tokens >= 0) & (tokens < 16)).all())

    @staticmethod
    def _generator(seed: int) -> torch.Generator:
        generator = torch.Generator(device="cpu")
        generator.manual_seed(seed)
        return generator


class TestStopTokens:
    """Stop-token detection used by generation loops."""

    def test_eos_is_a_stop_token(self) -> None:
        sampler = Sampler(eosTokenId=5)
        assert sampler.isStopToken(5)

    def test_explicit_stop_tokens(self) -> None:
        sampler = Sampler(stopTokenIds=[7, 9])
        assert sampler.isStopToken(7)
        assert sampler.isStopToken(9)
        assert not sampler.isStopToken(8)
