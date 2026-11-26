# apps/modules/model/ml/attention.py
"""Causal multi-head attention with optional grouped-query and KV cache."""

from __future__ import annotations

import math

import torch
from torch import nn
from torch.nn import functional as F

from ..models.modelModel import ModelConfig
from .embedding import RotaryEmbedding, applyRotaryEmbedding

KVCache = tuple[torch.Tensor, torch.Tensor]


class MultiHeadAttention(nn.Module):
    """Self-attention with causal masking, RoPE and GQA support."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.nHeads = config.nHeads
        self.nKvHeads = config.resolvedKvHeads
        if self.nHeads % self.nKvHeads != 0:
            raise ValueError(
                f"nHeads ({self.nHeads}) must be a multiple of nKvHeads ({self.nKvHeads})"
            )
        self.headDim = config.headDim
        self.dropoutP = config.attnDropout
        self.attnImpl = config.attnImpl

        self.qProj = nn.Linear(config.dim, self.nHeads * self.headDim, bias=config.useBias)
        self.kProj = nn.Linear(config.dim, self.nKvHeads * self.headDim, bias=config.useBias)
        self.vProj = nn.Linear(config.dim, self.nKvHeads * self.headDim, bias=config.useBias)
        self.oProj = nn.Linear(self.nHeads * self.headDim, config.dim, bias=config.useBias)

        self.rope: RotaryEmbedding | None = None
        if config.useRoPE:
            scalingFactor = 1.0
            if config.ropeScaling:
                scalingFactor = float(config.ropeScaling.get("factor", 1.0))
            self.rope = RotaryEmbedding(
                headDim=self.headDim,
                maxSeqLen=config.maxSeqLen,
                theta=config.ropeTheta,
                scalingFactor=scalingFactor,
            )

    def forward(
        self,
        hiddenStates: torch.Tensor,
        pastKeyValue: KVCache | None = None,
        useCache: bool = False,
    ) -> tuple[torch.Tensor, KVCache | None]:
        """Attend to the current tokens, optionally reusing a KV cache."""
        batchSize, seqLen, _ = hiddenStates.shape
        pastLen = pastKeyValue[0].shape[2] if pastKeyValue is not None else 0
        totalLen = pastLen + seqLen
        if totalLen > (self.rope.maxSeqLen if self.rope else totalLen):
            raise ValueError(f"Sequence length {totalLen} exceeds the model context window")

        query = (
            self.qProj(hiddenStates)
            .view(batchSize, seqLen, self.nHeads, self.headDim)
            .transpose(1, 2)
        )
        key = (
            self.kProj(hiddenStates)
            .view(batchSize, seqLen, self.nKvHeads, self.headDim)
            .transpose(1, 2)
        )
        value = (
            self.vProj(hiddenStates)
            .view(batchSize, seqLen, self.nKvHeads, self.headDim)
            .transpose(1, 2)
        )

        if self.rope is not None:
            cos, sin = self.rope(
                seqLen,
                offset=pastLen,
                device=hiddenStates.device,
                dtype=query.dtype,
            )
            query = applyRotaryEmbedding(query, cos, sin)
            key = applyRotaryEmbedding(key, cos, sin)

        if pastKeyValue is not None:
            key = torch.cat((pastKeyValue[0], key), dim=2)
            value = torch.cat((pastKeyValue[1], value), dim=2)

        nextCache: KVCache | None = (key, value) if useCache else None

        if self.nKvHeads != self.nHeads:
            repeats = self.nHeads // self.nKvHeads
            key = key.repeat_interleave(repeats, dim=1)
            value = value.repeat_interleave(repeats, dim=1)

        attentionMask = self._buildCausalMask(seqLen, pastLen, totalLen, hiddenStates.device)
        attended = self._attend(query, key, value, attentionMask, pastLen)
        attended = (
            attended.transpose(1, 2)
            .contiguous()
            .view(batchSize, seqLen, self.nHeads * self.headDim)
        )
        return self.oProj(attended), nextCache

    def _attend(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attentionMask: torch.Tensor | None,
        pastLen: int,
    ) -> torch.Tensor:
        """Run scaled dot-product attention, preferring PyTorch SDPA."""
        dropoutP = self.dropoutP if self.training else 0.0
        if self.attnImpl in {"sdpa", "flash"} and hasattr(F, "scaled_dot_product_attention"):
            if attentionMask is None:
                return F.scaled_dot_product_attention(
                    query,
                    key,
                    value,
                    dropout_p=dropoutP,
                    is_causal=query.shape[2] > 1,
                )
            return F.scaled_dot_product_attention(
                query,
                key,
                value,
                attn_mask=attentionMask,
                dropout_p=dropoutP,
            )

        scale = 1.0 / math.sqrt(query.shape[-1])
        scores = torch.matmul(query, key.transpose(-2, -1)) * scale
        if attentionMask is not None:
            scores = scores.masked_fill(~attentionMask, float("-inf"))
        elif pastLen == 0 and query.shape[2] > 1:
            causal = torch.ones(
                query.shape[2], key.shape[2], dtype=torch.bool, device=query.device
            ).tril()
            scores = scores.masked_fill(~causal, float("-inf"))
        probabilities = F.softmax(scores, dim=-1)
        probabilities = F.dropout(probabilities, p=dropoutP, training=self.training)
        return torch.matmul(probabilities, value)

    @staticmethod
    def _buildCausalMask(
        seqLen: int,
        pastLen: int,
        totalLen: int,
        device: torch.device,
    ) -> torch.Tensor | None:
        """Return a `(seqLen, totalLen)` keep-mask when a cache is in use."""
        if pastLen == 0:
            return None
        queryPositions = torch.arange(seqLen, device=device).unsqueeze(1) + pastLen
        keyPositions = torch.arange(totalLen, device=device).unsqueeze(0)
        return keyPositions <= queryPositions
