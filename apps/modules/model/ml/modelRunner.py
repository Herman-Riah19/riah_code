# apps/modules/model/ml/modelRunner.py
"""High-level interface around a TransformerLM (device, precision, checkpoints)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import torch

from ..models.modelModel import Checkpoint, GenerationOptions, ModelConfig
from .sampler import Sampler
from .transformer import TransformerLM

if TYPE_CHECKING:  # pragma: no cover - typing only
    from apps.modules.tokenizer.models.tokenizerModel import BPETokenizer

_DTYPE_MAP: dict[str, torch.dtype] = {
    "fp32": torch.float32,
    "fp16": torch.float16,
    "bf16": torch.bfloat16,
}


class ModelRunner:
    """Owns a model instance and exposes forward/generate/checkpoint helpers."""

    def __init__(
        self,
        config: ModelConfig,
        device: torch.device | None = None,
        tokenizer: BPETokenizer | None = None,
    ) -> None:
        self._config = config
        self._device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._dtype = self._resolveDtype(config.dtype)
        self._tokenizer = tokenizer

        model: torch.nn.Module = TransformerLM(config)
        model = model.to(self._device)
        model.eval()
        if config.compileMode is not None and hasattr(torch, "compile"):
            model = torch.compile(model, mode=config.compileMode)
        self._model = model

    @property
    def model(self) -> torch.nn.Module:
        """The underlying (possibly compiled) model."""
        return self._model

    @property
    def config(self) -> ModelConfig:
        """Architecture configuration of the loaded model."""
        return self._config

    @property
    def device(self) -> torch.device:
        """Device the model lives on."""
        return self._device

    @property
    def dtype(self) -> torch.dtype:
        """Compute dtype actually used for inference."""
        return self._dtype

    def setTokenizer(self, tokenizer: BPETokenizer | None) -> None:
        """Attach the tokenizer used to resolve stop sequences at generation time."""
        self._tokenizer = tokenizer

    def _resolveDtype(self, dtypeName: str) -> torch.dtype:
        """CPU does not support fp16 reliably, so fall back to fp32 there."""
        dtype = _DTYPE_MAP.get(dtypeName, torch.float32)
        if self._device.type == "cpu" and dtype is not torch.float32:
            return torch.float32
        return dtype

    @contextmanager
    def _inferenceContext(self) -> Iterator[None]:
        """Inference mode plus CUDA autocast when relevant."""
        with torch.inference_mode():
            if self._device.type == "cuda" and self._dtype is not torch.float32:
                with torch.autocast(device_type="cuda", dtype=self._dtype):
                    yield
            else:
                yield

    def forward(self, inputIds: torch.Tensor) -> torch.Tensor:
        """Return the logits for a batch of token ids."""
        self._model.eval()
        with self._inferenceContext():
            logits, _ = self._model(inputIds.to(self._device))
        return logits

    def buildSampler(self, options: GenerationOptions) -> Sampler:
        """Create a sampler, resolving stop sequences through the tokenizer."""
        stopTokenIds = [self._config.eosTokenId]
        if self._tokenizer is not None:
            for sequence in options.stopSequences:
                ids = self._tokenizer.encode(sequence, addSpecialTokens=False)
                stopTokenIds.extend(ids)

        generator = None
        if options.seed is not None:
            generator = torch.Generator(device=self._device)
            generator.manual_seed(options.seed)

        return Sampler(
            temperature=options.temperature,
            topK=options.topK,
            topP=options.topP,
            repetitionPenalty=options.repetitionPenalty,
            stopTokenIds=stopTokenIds,
            eosTokenId=self._config.eosTokenId,
            generator=generator,
        )

    def streamGenerate(
        self,
        inputIds: torch.Tensor,
        options: GenerationOptions,
    ) -> Iterator[int]:
        """Yield generated token ids one at a time."""
        sampler = self.buildSampler(options)
        self._model.eval()
        with self._inferenceContext():
            yield from self._model.stream_generate(inputIds, options.maxTokens, sampler)

    def generate(
        self,
        inputIds: torch.Tensor,
        options: GenerationOptions,
    ) -> torch.Tensor:
        """Return the prompt followed by the generated token ids."""
        sampler = self.buildSampler(options)
        self._model.eval()
        with self._inferenceContext():
            return self._model.generate(inputIds.to(self._device), options.maxTokens, sampler)

    def loadCheckpoint(self, checkpoint: Checkpoint) -> None:
        """Load model weights from a checkpoint file."""
        state = torch.load(
            checkpoint.path,
            map_location=self._device,
            weights_only=False,
        )
        weights = state.get("model", state) if isinstance(state, dict) else state
        self._model.load_state_dict(weights)
        self._model.eval()

    def saveCheckpoint(
        self,
        path: Path,
        optimizer: torch.optim.Optimizer | None = None,
        scheduler: Any | None = None,
        step: int = 0,
        epoch: int = 0,
        rng: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Path:
        """Persist model (and optionally optimizer/scheduler/RNG) state."""
        path.parent.mkdir(parents=True, exist_ok=True)
        state: dict[str, Any] = {
            "model": self._model.state_dict(),
            "modelConfig": self._config.toDict(),
            "optimizer": optimizer.state_dict() if optimizer is not None else None,
            "scheduler": scheduler.state_dict() if scheduler is not None else None,
            "step": step,
            "epoch": epoch,
            "rng": rng,
        }
        if extra:
            state.update(extra)
        torch.save(state, path)
        return path

    def numParameters(self) -> int:
        """Count the parameters of the loaded model."""
        return sum(parameter.numel() for parameter in self._model.parameters())
