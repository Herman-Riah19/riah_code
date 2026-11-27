"""Build optimizer, scheduler, precision scaler and data loaders for training."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, cast

import torch
from torch.optim import AdamW, Optimizer
from torch.optim.lr_scheduler import LambdaLR, LRScheduler
from torch.utils.data import DataLoader

from ..models.trainingModel import TrainingConfig
from .shardedDataset import ShardedTokenDataset

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..ml.modelRunner import ModelRunner


class Lion(Optimizer):
    """Minimal Lion optimizer (sign momentum with decoupled weight decay)."""

    def __init__(
        self,
        params: Iterator[torch.nn.Parameter] | list[torch.nn.Parameter],
        lr: float = 1e-4,
        betas: tuple[float, float] = (0.9, 0.99),
        weight_decay: float = 0.0,
    ) -> None:
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        defaults = {"lr": lr, "betas": betas, "weight_decay": weight_decay}
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(  # type: ignore[override]
        self,
        closure: Callable[[], torch.Tensor] | None = None,
    ) -> torch.Tensor | None:
        """Apply one Lion update to every parameter with a gradient."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            learningRate = float(group["lr"])
            beta1, beta2 = group["betas"]
            weightDecay = float(group["weight_decay"])
            for parameter in group["params"]:
                if parameter.grad is None:
                    continue
                gradient = parameter.grad
                state = self.state[parameter]
                if not state:
                    state["exp_avg"] = torch.zeros_like(parameter)
                expAvg = state["exp_avg"]
                update = expAvg.mul(beta1).add(gradient, alpha=1 - beta1).sign_()
                if weightDecay:
                    parameter.mul_(1 - learningRate * weightDecay)
                parameter.add_(update, alpha=-learningRate)
                expAvg.mul_(beta2).add_(gradient, alpha=1 - beta2)
        return loss


class TrainingSetup:
    """Create the model-specific resources required by one training loop."""

    def __init__(self, config: TrainingConfig, modelRunner: ModelRunner) -> None:
        self._config = config
        self._model = modelRunner.model
        self._device = modelRunner.device
        self._dtype = modelRunner.dtype

    def createOptimizer(self) -> Optimizer:
        """Build the optimizer selected by the configuration."""
        parameters = [
            parameter for parameter in self._model.parameters() if parameter.requires_grad
        ]
        if not parameters:
            raise ValueError("Le modele n'expose aucun parametre entrainable")

        config = self._config
        betas = (config.beta1, config.beta2)
        if config.optimizer == "lion":
            return Lion(
                parameters,
                lr=config.lr,
                betas=betas,
                weight_decay=config.weightDecay,
            )
        if config.optimizer == "adamw8bit":
            try:
                import bitsandbytes as bnb  # type: ignore[import-not-found]  # noqa: PLC0415

                return cast(
                    "Optimizer",
                    bnb.optim.AdamW8bit(
                        parameters,
                        lr=config.lr,
                        betas=betas,
                        eps=config.eps,
                        weight_decay=config.weightDecay,
                    ),
                )
            except (ImportError, RuntimeError):
                # bitsandbytes needs a CUDA build; fall back to plain AdamW.
                pass
        return AdamW(
            parameters,
            lr=config.lr,
            betas=betas,
            eps=config.eps,
            weight_decay=config.weightDecay,
        )

    def createScheduler(self, optimizer: Optimizer) -> LRScheduler:
        """Warmup + cosine/constant/wsd schedule expressed as a LambdaLR."""
        return LambdaLR(optimizer, lr_lambda=self._lrScale)

    def _lrScale(self, step: int) -> float:
        """Return the learning-rate multiplier for one optimizer step."""
        config = self._config
        warmup = 0
        if config.scheduler in {"cosine_warmup", "wsd"}:
            warmup = max(0, config.warmupSteps)
        if warmup and step < warmup:
            return (step + 1) / warmup

        floor = 0.0
        if config.lr > 0:
            floor = min(1.0, max(0.0, config.minLr / config.lr))
        if config.scheduler == "constant":
            return 1.0
        if config.scheduler == "wsd":
            total = max(config.maxSteps, warmup + 1)
            decayStart = total - max(1, total // 10)
            if step < decayStart:
                return 1.0
            progress = (step - decayStart) / max(1, total - decayStart)
            return floor + (1.0 - floor) * (1.0 - min(1.0, progress))

        decaySteps = max(1, config.decaySteps)
        progress = min(1.0, max(0.0, (step - warmup) / max(1, decaySteps - warmup)))
        cosine = 0.5 * (1.0 + math.cos(math.pi * progress))
        return floor + (1.0 - floor) * cosine

    def createScaler(self) -> torch.amp.GradScaler:
        """GradScaler is only useful for fp16 on CUDA."""
        enabled = (
            self._config.useGradScaler
            and self._dtype is torch.float16
            and self._device.type == "cuda"
        )
        deviceType = "cuda" if self._device.type == "cuda" else "cpu"
        return torch.amp.GradScaler(deviceType, enabled=enabled)

    def createLoader(
        self,
        shards: list[Path],
        shuffle: bool,
    ) -> DataLoader | None:
        """Build an iterable loader over the given shards."""
        if not shards:
            return None
        config = self._config
        dataset = ShardedTokenDataset(
            shards,
            seqLen=config.seqLen,
            shuffle=shuffle,
            seed=config.seed,
            vocabSize=config.modelConfig.vocabSize,
        )
        return DataLoader(
            dataset,
            batch_size=config.microBatchSize or config.batchSize,
            num_workers=max(0, config.numWorkers),
            pin_memory=self._device.type == "cuda",
            drop_last=True,
            persistent_workers=False,
        )

    @contextmanager
    def autocast(self) -> Iterator[None]:
        """Enable CUDA autocast when the model runs in fp16/bf16."""
        if self._device.type == "cuda" and self._dtype is not torch.float32:
            with torch.autocast(device_type="cuda", dtype=self._dtype):
                yield
        else:
            yield


__all__ = ["Lion", "TrainingSetup"]
