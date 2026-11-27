# apps/modules/model/pipelines/trainingLoop.py
"""Training loop with mixed precision, gradient accumulation and checkpointing."""

from __future__ import annotations

import json
import math
import random
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any

import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_

from ..models.trainingModel import Checkpoint, TrainingConfig, TrainingResult
from ..repositories.checkpointRepository import CheckpointRepository
from .shardedDataset import ShardedTokenDataset
from .trainingSetup import Lion, TrainingSetup

if TYPE_CHECKING:  # pragma: no cover - typing only
    from apps.modules.tokenizer.models.tokenizerModel import BPETokenizer

    from ..ml.modelRunner import ModelRunner

ProgressCallback = Callable[[dict[str, Any]], None]


class CancellationToken:
    """Cooperative cancellation flag shared between a service and its loop."""

    def __init__(self) -> None:
        self._event = Event()

    @property
    def isCancelled(self) -> bool:
        """True once `cancel()` has been called."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Ask the training loop to stop at the next safe point."""
        self._event.set()

    def reset(self) -> None:
        """Clear the cancellation request."""
        self._event.clear()


class TrainingLoop:
    """Run a supervised next-token training job on pre-tokenized shards."""

    def __init__(
        self,
        config: TrainingConfig,
        modelRunner: ModelRunner,
        tokenizer: BPETokenizer | None = None,
        checkpointRepo: CheckpointRepository | None = None,
        runId: str | None = None,
        progressCallback: ProgressCallback | None = None,
    ) -> None:
        if config.seqLen < 1:
            raise ValueError("seqLen must be >= 1")
        if config.seqLen > config.modelConfig.maxSeqLen:
            raise ValueError(
                f"seqLen ({config.seqLen}) exceeds model maxSeqLen ({config.modelConfig.maxSeqLen})"
            )

        self._config = config
        self._modelRunner = modelRunner
        self._tokenizer = tokenizer
        self._checkpointRepo = checkpointRepo
        self._runId = runId
        self._progressCallback = progressCallback
        self._device: torch.device = modelRunner.device
        self._dtype: torch.dtype = modelRunner.dtype
        self._model = modelRunner.model

        self._setup = TrainingSetup(config, modelRunner)
        self.optimizer = self._setup.createOptimizer()
        self.scheduler = self._setup.createScheduler(self.optimizer)
        self.scaler = self._setup.createScaler()
        self.trainLoader = self._setup.createLoader(config.trainShards, shuffle=True)
        self.valLoader = (
            self._setup.createLoader(config.valShards, shuffle=False) if config.valShards else None
        )

        self.step = 0
        self.epoch = 0
        self.bestValLoss = float("inf")
        self.tokensSeen = 0
        self.lastLoss: float | None = None
        self.cancelled = False
        self.history: list[dict[str, Any]] = []
        self.cancelToken = CancellationToken()
        self.logFile = Path(config.checkpointDir) / "training_log.jsonl"

    # ------------------------------------------------------------------ setup

    @property
    def config(self) -> TrainingConfig:
        """Training configuration of this loop."""
        return self._config

    @property
    def model(self) -> torch.nn.Module:
        """Underlying (possibly compiled) model."""
        return self._model

    @property
    def device(self) -> torch.device:
        """Device the model lives on."""
        return self._device

    # --------------------------------------------------------------- training

    def train(self) -> TrainingResult:
        """Run until `maxSteps`, cancellation or `maxEpochs` are reached."""
        if self.trainLoader is None:
            raise ValueError("Aucun shard d'entrainement fourni")
        startedAt = time.perf_counter()
        self._model.train()
        dataIterator = self._newEpochIterator()
        accumulation = max(1, self._config.gradientAccumulationSteps)

        while self.step < self._config.maxSteps:
            if self.cancelToken.isCancelled:
                self.cancelled = True
                break

            self.optimizer.zero_grad(set_to_none=True)
            accumulatedLoss = 0.0
            microSteps = 0
            exhausted = False

            for _ in range(accumulation):
                try:
                    batch = next(dataIterator)
                except StopIteration:
                    self._advanceEpoch()
                    if self._maxEpochsReached():
                        exhausted = True
                        break
                    dataIterator = self._newEpochIterator()
                    try:
                        batch = next(dataIterator)
                    except StopIteration:
                        exhausted = True
                        break

                accumulatedLoss += self._trainingStep(batch, accumulation)
                microSteps += 1
                self.tokensSeen += int(batch["input_ids"].size(0)) * self._config.seqLen

            if exhausted or microSteps == 0:
                self.optimizer.zero_grad(set_to_none=True)
                break

            self._applyGradients()
            self.scheduler.step()
            self.step += 1
            self.lastLoss = accumulatedLoss / microSteps
            self._afterStep()

        tag = "cancelled" if self.cancelled else "final"
        self.saveCheckpoint(tag)
        bestValLoss = (
            self.bestValLoss if math.isfinite(self.bestValLoss) else (self.lastLoss or 0.0)
        )
        return TrainingResult(
            steps=self.step,
            bestValLoss=bestValLoss,
            tokensSeen=self.tokensSeen,
            elapsedSeconds=time.perf_counter() - startedAt,
            finalLoss=self.lastLoss,
        )

    def _trainingStep(self, batch: dict[str, torch.Tensor], accumulation: int) -> float:
        """Forward + backward one micro-batch and return its unscaled loss."""
        inputIds = batch["input_ids"].to(self._device, non_blocking=True)
        targets = batch["labels"].to(self._device, non_blocking=True)
        with self._setup.autocast():
            _, loss = self._model(inputIds, targets)
            if loss is None:  # pragma: no cover - defensive
                raise RuntimeError("le modele n'a pas retourne de loss")
            scaledLoss = loss / accumulation
        if self.scaler.is_enabled():
            self.scaler.scale(scaledLoss).backward()
        else:
            scaledLoss.backward()
        return float(loss.detach())

    def _applyGradients(self) -> None:
        """Clip gradients then run one optimizer step."""
        if self.scaler.is_enabled():
            self.scaler.unscale_(self.optimizer)
        if self._config.gradClip > 0:
            clip_grad_norm_(self._model.parameters(), self._config.gradClip)
        if self.scaler.is_enabled():
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            self.optimizer.step()

    def _afterStep(self) -> None:
        """Log metrics, evaluate and checkpoint at the configured intervals."""
        config = self._config
        if config.logInterval > 0 and self.step % config.logInterval == 0:
            self._logMetrics({"loss": self.lastLoss})

        if config.evalInterval > 0 and self.step % config.evalInterval == 0:
            valLoss = self.evaluate()
            if valLoss is not None:
                self._logMetrics({"valLoss": valLoss}, prefix="val")
                if valLoss < self.bestValLoss:
                    self.bestValLoss = valLoss
                    self.saveCheckpoint("best")

        if config.checkpointInterval > 0 and self.step % config.checkpointInterval == 0:
            self.saveCheckpoint(f"step_{self.step}")

        self._notifyProgress()

    def _advanceEpoch(self) -> None:
        """Move to the next epoch."""
        self.epoch += 1

    def _maxEpochsReached(self) -> bool:
        """Return True when the configured epoch budget is exhausted."""
        maxEpochs = self._config.maxEpochs
        return maxEpochs is not None and self.epoch >= maxEpochs

    def _newEpochIterator(self) -> Iterator[dict[str, torch.Tensor]]:
        """Start a fresh pass over the training shards."""
        if self.trainLoader is None:  # pragma: no cover - checked by train()
            raise ValueError("Aucun shard d'entrainement fourni")
        dataset = self.trainLoader.dataset
        if isinstance(dataset, ShardedTokenDataset):
            dataset.setEpoch(self.epoch)
        return iter(self.trainLoader)

    @torch.inference_mode()
    def evaluate(self) -> float | None:
        """Return the mean validation loss, or None without validation shards."""
        if self.valLoader is None:
            return None

        wasTraining = self._model.training
        self._model.eval()
        total = 0.0
        batches = 0
        try:
            for index, batch in enumerate(self.valLoader):
                if index >= self._config.evalSteps:
                    break
                inputIds = batch["input_ids"].to(self._device, non_blocking=True)
                targets = batch["labels"].to(self._device, non_blocking=True)
                with self._setup.autocast():
                    _, loss = self._model(inputIds, targets)
                if loss is None:  # pragma: no cover - defensive
                    continue
                total += float(loss)
                batches += 1
        finally:
            self._model.train(wasTraining)

        return total / batches if batches else None

    # ------------------------------------------------------------- checkpoints

    def saveCheckpoint(self, tag: str) -> Path:
        """Persist model/optimizer/scheduler/RNG state and index it."""
        checkpointDir = Path(self._config.checkpointDir)
        checkpointDir.mkdir(parents=True, exist_ok=True)
        path = checkpointDir / f"checkpoint_{tag}.pt"
        bestValLoss = self.bestValLoss if math.isfinite(self.bestValLoss) else None

        self._modelRunner.saveCheckpoint(
            path,
            optimizer=self.optimizer if self._config.saveOptimizer else None,
            scheduler=self.scheduler,
            step=self.step,
            epoch=self.epoch,
            rng=self._captureRng() if self._config.saveRng else None,
            extra={
                "loss": self.lastLoss,
                "bestValLoss": bestValLoss,
                "tokensSeen": self.tokensSeen,
                "modelName": self._config.modelName,
                "trainingConfig": self._config.toDict(),
            },
        )

        if self._checkpointRepo is not None:
            checkpoint = Checkpoint(
                id=self._checkpointId(tag),
                path=path,
                step=self.step,
                epoch=self.epoch,
                loss=self.lastLoss or 0.0,
                valLoss=bestValLoss,
                modelConfig=self._config.modelConfig,
                trainingConfig=self._config,
                createdAt=datetime.now(UTC),
                isBest=tag == "best",
                modelName=self._config.modelName,
                metadata={"tag": tag, "runId": self._runId},
            )
            self._checkpointRepo.save(checkpoint)
            self._checkpointRepo.pruneOld(
                keepLastN=self._config.keepLastNCheckpoints,
                modelName=self._config.modelName,
            )
        return path

    def loadCheckpoint(self, checkpoint: Checkpoint | Path) -> None:
        """Restore model, optimizer, scheduler, counters and RNG state."""
        path = checkpoint.path if isinstance(checkpoint, Checkpoint) else Path(checkpoint)
        state = torch.load(path, map_location=self._device, weights_only=False)
        if not isinstance(state, dict) or "model" not in state:
            raise ValueError(f"Checkpoint invalide (poids absents): {path}")

        self._model.load_state_dict(state["model"])
        if state.get("optimizer") and self._config.saveOptimizer:
            self.optimizer.load_state_dict(state["optimizer"])
        if state.get("scheduler"):
            self.scheduler.load_state_dict(state["scheduler"])

        self.step = int(state.get("step", 0))
        self.epoch = int(state.get("epoch", 0))
        bestValLoss = state.get("bestValLoss", state.get("best_val_loss"))
        self.bestValLoss = float(bestValLoss) if bestValLoss is not None else float("inf")
        self.tokensSeen = int(state.get("tokensSeen", 0))
        loss = state.get("loss")
        self.lastLoss = float(loss) if loss is not None else None

        rng = state.get("rng")
        if rng and self._config.saveRng:
            self._restoreRng(rng)

        dataset = self.trainLoader.dataset if self.trainLoader is not None else None
        if isinstance(dataset, ShardedTokenDataset):
            dataset.setEpoch(self.epoch)

    def _checkpointId(self, tag: str) -> str:
        """Stable checkpoint identifier, unique per run and tag."""
        prefix = self._runId or self._config.modelName or "run"
        return f"{prefix}:{tag}"

    @staticmethod
    def _captureRng() -> dict[str, Any]:
        """Capture Python/NumPy/Torch (and CUDA) RNG states."""
        return {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
            "cuda": (torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None),
        }

    @staticmethod
    def _restoreRng(rng: dict[str, Any]) -> None:
        """Restore the RNG states captured by `_captureRng`."""
        pythonState = rng.get("python")
        if pythonState is not None:
            random.setstate(pythonState)
        numpyState = rng.get("numpy")
        if numpyState is not None:
            np.random.set_state(numpyState)
        torchState = rng.get("torch")
        if torchState is not None:
            torch.set_rng_state(torchState.to("cpu"))
        cudaState = rng.get("cuda")
        if cudaState and torch.cuda.is_available():
            torch.cuda.set_rng_state_all([state.to("cpu") for state in cudaState])

    # ----------------------------------------------------------------- control

    def cancel(self) -> None:
        """Request a graceful stop at the next optimizer step."""
        self.cancelToken.cancel()

    def snapshot(self) -> dict[str, Any]:
        """Return the live training state, suitable for `Job.progress`."""
        maxSteps = max(1, self._config.maxSteps)
        bestValLoss = self.bestValLoss if math.isfinite(self.bestValLoss) else None
        return {
            "step": self.step,
            "epoch": self.epoch,
            "maxSteps": self._config.maxSteps,
            "progress": min(1.0, self.step / maxSteps),
            "loss": self.lastLoss,
            "bestValLoss": bestValLoss,
            "tokensSeen": self.tokensSeen,
            "learningRate": float(self.optimizer.param_groups[0]["lr"]),
            "cancelled": self.cancelled,
        }

    def _notifyProgress(self) -> None:
        """Push a progress snapshot to the owning service, if any."""
        if self._progressCallback is None:
            return
        try:
            self._progressCallback(self.snapshot())
        except Exception:  # noqa: BLE001 - progress must never stop training
            return

    def _logMetrics(
        self,
        metrics: dict[str, Any],
        prefix: str = "train",
    ) -> None:
        """Append one metrics entry to memory and to `training_log.jsonl`."""
        entry = {
            "step": self.step,
            "epoch": self.epoch,
            "learningRate": float(self.optimizer.param_groups[0]["lr"]),
            **{f"{prefix}/{key}": value for key, value in metrics.items()},
        }
        self.history.append(entry)
        try:
            self.logFile.parent.mkdir(parents=True, exist_ok=True)
            with self.logFile.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            return


__all__ = ["CancellationToken", "Lion", "TrainingLoop"]
