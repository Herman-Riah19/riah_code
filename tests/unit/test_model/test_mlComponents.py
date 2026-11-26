# tests/unit/test_model/test_mlComponents.py
"""Tests for the pure ML components (norms, RoPE, attention, FFN, loss)."""

from __future__ import annotations

import math

import pytest
import torch
from tinyModel import tinyModelConfig
from torch.nn import functional as F

from apps.modules.model.ml.attention import MultiHeadAttention
from apps.modules.model.ml.embedding import (
    RotaryEmbedding,
    applyRotaryEmbedding,
    rotateHalf,
)
from apps.modules.model.ml.feedForward import GeGLU, GELUMlp, SwiGLU, buildFeedForward
from apps.modules.model.ml.loss import crossEntropyLoss, perplexity
from apps.modules.model.ml.normalization import (
    LayerNormBlock,
    RMSNorm,
    buildNormalization,
)
from apps.modules.model.ml.transformer import TransformerBlock, TransformerLM


class TestNormalization:
    """Normalization layers keep shapes and neutral statistics."""

    def test_rms_norm_unit_rms(self) -> None:
        norm = RMSNorm(16)
        values = torch.randn(2, 5, 16)
        output = norm(values)
        assert output.shape == values.shape
        rms = output.pow(2).mean(dim=-1)
        torch.testing.assert_close(rms, torch.ones_like(rms), atol=1e-4, rtol=1e-4)

    def test_layer_norm_zero_mean(self) -> None:
        norm = LayerNormBlock(16)
        output = norm(torch.randn(3, 4, 16))
        torch.testing.assert_close(
            output.mean(dim=-1),
            torch.zeros(3, 4),
            atol=1e-5,
            rtol=1e-5,
        )

    def test_build_normalization_selects_variant(self) -> None:
        assert isinstance(buildNormalization(tinyModelConfig()), RMSNorm)
        assert isinstance(
            buildNormalization(tinyModelConfig(normType="layernorm")),
            LayerNormBlock,
        )


class TestRotaryEmbedding:
    """RoPE tables and rotation properties."""

    def test_tables_have_expected_shape(self) -> None:
        rope = RotaryEmbedding(headDim=8, maxSeqLen=32)
        cos, sin = rope(4)
        assert cos.shape == (4, 8)
        assert sin.shape == (4, 8)

    def test_offset_slices_the_cache(self) -> None:
        rope = RotaryEmbedding(headDim=8, maxSeqLen=32)
        fullCos, _ = rope(4)
        offsetCos, _ = rope(2, offset=2)
        torch.testing.assert_close(offsetCos, fullCos[2:])

    def test_rejects_odd_head_dim(self) -> None:
        with pytest.raises(ValueError, match="even"):
            RotaryEmbedding(headDim=7, maxSeqLen=8)

    def test_rejects_sequences_beyond_cache(self) -> None:
        rope = RotaryEmbedding(headDim=8, maxSeqLen=4)
        with pytest.raises(ValueError, match="exceeds"):
            rope(2, offset=3)

    def test_rotation_preserves_norm(self) -> None:
        rope = RotaryEmbedding(headDim=8, maxSeqLen=8)
        cos, sin = rope(4)
        values = torch.randn(1, 2, 4, 8)
        rotated = applyRotaryEmbedding(values, cos, sin)
        torch.testing.assert_close(
            rotated.norm(dim=-1),
            values.norm(dim=-1),
            atol=1e-5,
            rtol=1e-5,
        )

    def test_rotate_half_swaps_halves(self) -> None:
        values = torch.tensor([[1.0, 2.0, 3.0, 4.0]])
        torch.testing.assert_close(
            rotateHalf(values),
            torch.tensor([[-3.0, -4.0, 1.0, 2.0]]),
        )


class TestAttention:
    """Attention shapes, causality and grouped-query support."""

    def test_output_shape(self, tinyConfig) -> None:
        attention = MultiHeadAttention(tinyConfig)
        hidden = torch.randn(2, 6, tinyConfig.dim)
        output, cache = attention(hidden)
        assert output.shape == hidden.shape
        assert cache is None

    def test_causal_mask_hides_future_tokens(self, tinyModel) -> None:
        tokenIds = torch.randint(0, 64, (1, 6))
        perturbed = tokenIds.clone()
        perturbed[:, -1] = (perturbed[:, -1] + 1) % 64

        with torch.no_grad():
            first, _ = tinyModel(tokenIds)
            second, _ = tinyModel(perturbed)

        torch.testing.assert_close(first[:, :-1], second[:, :-1])

    def test_grouped_query_attention_shape(self) -> None:
        config = tinyModelConfig(nHeads=4, nKvHeads=1, dim=32)
        attention = MultiHeadAttention(config)
        output, _ = attention(torch.randn(2, 5, config.dim))
        assert output.shape == (2, 5, config.dim)

    def test_cache_grows_with_tokens(self, tinyConfig) -> None:
        attention = MultiHeadAttention(tinyConfig)
        _, cache = attention(torch.randn(1, 3, tinyConfig.dim), useCache=True)
        assert cache is not None
        assert cache[0].shape[2] == 3
        _, cache = attention(
            torch.randn(1, 2, tinyConfig.dim),
            pastKeyValue=cache,
            useCache=True,
        )
        assert cache is not None
        assert cache[0].shape[2] == 5


class TestFeedForward:
    """Feed-forward variants preserve the hidden dimension."""

    @pytest.mark.parametrize(
        "module",
        [
            SwiGLU(16, 32),
            GeGLU(16, 32),
            GELUMlp(16, 32),
        ],
    )
    def test_variant_shapes(self, module: torch.nn.Module) -> None:
        assert module(torch.randn(2, 5, 16)).shape == (2, 5, 16)

    def test_build_feed_forward_selects_variant(self) -> None:
        assert isinstance(buildFeedForward(tinyModelConfig()), SwiGLU)
        assert isinstance(buildFeedForward(tinyModelConfig(activation="gelu")), GELUMlp)
        assert isinstance(buildFeedForward(tinyModelConfig(activation="geglu")), GeGLU)


class TestLoss:
    """Cross entropy matches PyTorch and supports smoothing."""

    def test_matches_torch_cross_entropy(self) -> None:
        logits = torch.randn(2, 4, 10)
        targets = torch.randint(0, 10, (2, 4))
        expected = F.cross_entropy(logits.reshape(-1, 10), targets.reshape(-1))
        torch.testing.assert_close(crossEntropyLoss(logits, targets), expected)

    def test_label_smoothing_changes_value(self) -> None:
        logits = torch.randn(1, 3, 10)
        targets = torch.randint(0, 10, (1, 3))
        plain = crossEntropyLoss(logits, targets)
        smoothed = crossEntropyLoss(logits, targets, labelSmoothing=0.1)
        assert not math.isclose(float(plain), float(smoothed), rel_tol=1e-6)

    def test_rejects_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="share their leading"):
            crossEntropyLoss(torch.randn(2, 4, 10), torch.randint(0, 10, (2, 5)))

    def test_perplexity_is_exponential(self) -> None:
        assert math.isclose(perplexity(2.0), math.exp(2.0), rel_tol=1e-6)


class TestTransformer:
    """End-to-end forward, cache equivalence and gradients."""

    def test_forward_shapes_and_loss(self, tinyModel, tinyConfig) -> None:
        tokenIds = torch.randint(0, tinyConfig.vocabSize, (2, 8))
        logits, loss = tinyModel(tokenIds, tokenIds)
        assert logits.shape == (2, 8, tinyConfig.vocabSize)
        assert loss is not None
        assert torch.isfinite(loss)

    def test_forward_without_targets_has_no_loss(self, tinyModel) -> None:
        logits, loss = tinyModel(torch.randint(0, 64, (1, 4)))
        assert logits.shape == (1, 4, 64)
        assert loss is None

    def test_backward_populates_gradients(self, tinyModel) -> None:
        tokenIds = torch.randint(0, 64, (2, 8))
        _, loss = tinyModel(tokenIds, tokenIds)
        assert loss is not None
        loss.backward()
        gradients = [
            parameter.grad for parameter in tinyModel.parameters() if parameter.grad is not None
        ]
        assert gradients
        assert all(torch.isfinite(gradient).all() for gradient in gradients)

    def test_cached_forward_matches_full_forward(self, tinyModel) -> None:
        tokenIds = torch.randint(0, 64, (1, 8))
        with torch.no_grad():
            fullLogits, _ = tinyModel(tokenIds)
            cachedLogits, _ = tinyModel.forwardCached(tokenIds)
        torch.testing.assert_close(fullLogits, cachedLogits, atol=1e-5, rtol=1e-4)

    def test_incremental_cache_matches_suffix(self, tinyModel) -> None:
        tokenIds = torch.randint(0, 64, (1, 8))
        with torch.no_grad():
            fullLogits, _ = tinyModel(tokenIds)
            _, caches = tinyModel.forwardCached(tokenIds[:, :5])
            suffixLogits, _ = tinyModel.forwardCached(tokenIds[:, 5:], caches)
        torch.testing.assert_close(
            suffixLogits,
            fullLogits[:, 5:],
            atol=1e-5,
            rtol=1e-4,
        )

    def test_tied_embeddings_skip_lm_head(self, tinyModel) -> None:
        assert tinyModel.lmHead is None

    def test_untied_embeddings_use_lm_head(self) -> None:
        model = TransformerLM(tinyModelConfig(tieEmbeddings=False))
        assert model.lmHead is not None

    def test_parameter_count(self, tinyModel) -> None:
        assert tinyModel.numParameters() > 0

    def test_block_returns_cache_when_requested(self, tinyConfig) -> None:
        block = TransformerBlock(tinyConfig)
        hidden, cache = block(torch.randn(1, 3, tinyConfig.dim), useCache=True)
        assert hidden.shape == (1, 3, tinyConfig.dim)
        assert cache is not None
