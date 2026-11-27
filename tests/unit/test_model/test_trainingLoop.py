# tests/unit/test_model/test_trainingLoop.py
"""Tests for the training loop (schedules, evaluation, checkpoints, resume)."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest
import torch
from tinyModel import tinyModelConfig, tinyTrainingConfig
from tinyShards import writeTinyShard

from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.pipelines.trainingLoop import Lion, TrainingLoop
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from trainingLoopTestUtils import buildLoop


class TestTrainingLoopRun:
    """End-to-end training behaviour on CPU."""

    def test_train_returns_result(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=3)

        result = loop.train()

        assert result.steps == 3
        assert result.tokensSeen == 3 * 2 * 8
        assert result.finalLoss is not None
        assert torch.isfinite(torch.tensor(result.finalLoss))
        assert result.elapsedSeconds > 0

    def test_history_and_log_file(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=2, logInterval=1)

        loop.train()

        assert [entry["step"] for entry in loop.history] == [1, 2]
        assert all(entry["train/loss"] is not None for entry in loop.history)
        assert all(entry["learningRate"] > 0 for entry in loop.history)

        logLines = loop.logFile.read_text(encoding="utf-8").strip().splitlines()
        assert len(logLines) == 2
        assert json.loads(logLines[0])["step"] == 1

    def test_gradient_accumulation_counts_every_micro_batch(self, tmp_path: Path) -> None:
        loop = buildLoop(
            tmp_path,
            maxSteps=2,
            gradientAccumulationSteps=2,
        )

        result = loop.train()

        # 2 optimizer steps * 2 micro-batches * batch 2 * seqLen 8
        assert result.tokensSeen == 2 * 2 * 2 * 8

    def test_max_epochs_stops_after_one_pass(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=100, maxEpochs=1, checkpointInterval=0)

        result = loop.train()

        assert result.steps == 12  # 24 windows / batch size 2
        assert loop.epoch == 1

    def test_optimizer_variants(self, tmp_path: Path) -> None:
        lionLoop = buildLoop(tmp_path / "lion", optimizer="lion", maxSteps=1)
        assert isinstance(lionLoop.optimizer, Lion)

        fallbackLoop = buildLoop(tmp_path / "adamw8bit", optimizer="adamw8bit", maxSteps=1)
        assert isinstance(fallbackLoop.optimizer, torch.optim.Optimizer)


class TestTrainingLoopEvaluation:
    """Validation pass and best-checkpoint selection."""

    def test_evaluate_without_validation_shards(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=1)
        assert loop.evaluate() is None

    def test_evaluate_returns_a_finite_loss(self, tmp_path: Path) -> None:
        valShard = writeTinyShard(tmp_path / "data", name="val.bin", seed=23)
        loop = buildLoop(tmp_path, valShards=[valShard], maxSteps=1)

        loss = loop.evaluate()

        assert loss is not None
        assert torch.isfinite(torch.tensor(loss))

    def test_best_checkpoint_is_saved_and_indexed(self, tmp_path: Path) -> None:
        valShard = writeTinyShard(tmp_path / "data", name="val.bin", seed=23)
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(
            tmp_path,
            valShards=[valShard],
            checkpointRepo=repository,
            maxSteps=2,
            evalInterval=1,
        )

        loop.train()

        bestFile = Path(loop.config.checkpointDir) / "checkpoint_best.pt"
        assert bestFile.is_file()
        best = repository.findBest()
        assert best is not None
        assert best.isBest is True
        assert best.valLoss is not None


class TestTrainingLoopCheckpoints:
    """Checkpoint persistence, indexing and resume."""

    def test_saves_and_indexes_the_final_checkpoint(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(tmp_path, checkpointRepo=repository, maxSteps=2)

        loop.train()

        finalFile = Path(loop.config.checkpointDir) / "checkpoint_final.pt"
        assert finalFile.is_file()
        latest = repository.findLatest()
        assert latest is not None
        assert latest.step == 2
        assert latest.metadata["tag"] == "final"
        assert latest.trainingConfig is not None

    def test_state_contains_optimizer_rng_and_counters(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=1)
        loop.train()

        state = torch.load(
            Path(loop.config.checkpointDir) / "checkpoint_final.pt",
            map_location="cpu",
            weights_only=False,
        )

        assert state["model"]
        assert state["optimizer"] is not None
        assert state["scheduler"] is not None
        assert state["rng"]["torch"] is not None
        assert state["step"] == 1
        assert state["tokensSeen"] == 2 * 8

    def test_load_restores_counters_and_weights(self, tmp_path: Path) -> None:
        source = buildLoop(tmp_path, maxSteps=2)
        source.train()
        checkpointPath = Path(source.config.checkpointDir) / "checkpoint_final.pt"

        restored = buildLoop(tmp_path, maxSteps=2)
        restored.loadCheckpoint(checkpointPath)

        assert restored.step == 2
        assert restored.epoch == source.epoch
        assert restored.tokensSeen == source.tokensSeen
        for expected, actual in zip(
            source.model.state_dict().values(),
            restored.model.state_dict().values(),
            strict=True,
        ):
            torch.testing.assert_close(expected, actual)

    def test_resume_is_deterministic(self, tmp_path: Path) -> None:
        source = buildLoop(tmp_path, maxSteps=2)
        source.train()
        checkpointPath = Path(source.config.checkpointDir) / "checkpoint_final.pt"

        first = buildLoop(tmp_path, maxSteps=3, checkpointDir=tmp_path / "resume-a")
        first.loadCheckpoint(checkpointPath)
        firstResult = first.train()

        second = buildLoop(tmp_path, maxSteps=3, checkpointDir=tmp_path / "resume-b")
        second.loadCheckpoint(checkpointPath)
        secondResult = second.train()

        assert firstResult.steps == 3
        assert firstResult.finalLoss == secondResult.finalLoss
        assert first.tokensSeen == second.tokensSeen

    def test_resume_from_checkpoint_object(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path / "index")
        source = buildLoop(tmp_path, checkpointRepo=repository, maxSteps=2)
        source.train()
        checkpoint = repository.findLatest()
        assert checkpoint is not None

        restored = buildLoop(tmp_path, checkpointRepo=repository, maxSteps=2)
        restored.loadCheckpoint(checkpoint)

        assert restored.step == checkpoint.step

    def test_pruning_keeps_best_file_alive(self, tmp_path: Path) -> None:
        valShard = writeTinyShard(tmp_path / "data", name="val.bin", seed=23)
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(
            tmp_path,
            valShards=[valShard],
            checkpointRepo=repository,
            maxSteps=3,
            evalInterval=1,
            checkpointInterval=1,
            keepLastNCheckpoints=1,
        )

        loop.train()

        checkpoints = repository.listAll(limit=20)
        assert 1 <= len(checkpoints) <= 2
        assert repository.findBest() is not None
        for checkpoint in checkpoints:
            assert checkpoint.path.is_file()

    def test_invalid_checkpoint_raises(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=1)
        invalidPath = tmp_path / "invalid.pt"
        invalidPath.write_bytes(b"not a checkpoint")

        with pytest.raises((ValueError, pickle.UnpicklingError)):
            loop.loadCheckpoint(invalidPath)


class TestTrainingLoopControl:
    """Cancellation, snapshot and configuration guards."""

    def test_cancellation_before_training(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=3)
        loop.cancel()

        result = loop.train()

        assert result.steps == 0
        assert loop.cancelled is True
        assert (Path(loop.config.checkpointDir) / "checkpoint_cancelled.pt").is_file()

    def test_cancellation_during_training(self, tmp_path: Path) -> None:
        holder: dict[str, TrainingLoop] = {}

        def onProgress(snapshot: dict) -> None:
            if int(snapshot["step"]) >= 1:
                holder["loop"].cancel()

        loop = buildLoop(tmp_path, maxSteps=5, progressCallback=onProgress)
        holder["loop"] = loop

        result = loop.train()

        assert result.steps == 1
        assert loop.cancelled is True

    def test_snapshot_reports_progress(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=4)
        loop.train()

        snapshot = loop.snapshot()

        assert snapshot["step"] == 4
        assert snapshot["maxSteps"] == 4
        assert snapshot["progress"] == 1.0
        assert snapshot["cancelled"] is False
        assert snapshot["learningRate"] > 0

    def test_seq_len_above_context_is_rejected(self, tmp_path: Path) -> None:
        config = tinyTrainingConfig(
            modelConfig=tinyModelConfig(maxSeqLen=8),
            trainShards=[writeTinyShard(tmp_path)],
            seqLen=16,
            checkpointDir=tmp_path / "checkpoints",
            numWorkers=0,
            dtype="fp32",
        )
        runner = ModelRunner(config.modelConfig, device=torch.device("cpu"))

        with pytest.raises(ValueError, match="maxSeqLen"):
            TrainingLoop(config, runner)

    def test_missing_training_shards_are_rejected(self, tmp_path: Path) -> None:
        config = tinyTrainingConfig(
            trainShards=[],
            checkpointDir=tmp_path / "checkpoints",
            numWorkers=0,
            dtype="fp32",
        )
        runner = ModelRunner(config.modelConfig, device=torch.device("cpu"))
        loop = TrainingLoop(config, runner)

        with pytest.raises(ValueError, match="shard"):
            loop.train()


class FrozenRunner:
    """Minimal runner whose parameters are all frozen."""

    def __init__(self) -> None:
        self.device = torch.device("cpu")
        self.dtype = torch.float32
        self.model = torch.nn.Linear(2, 2)
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)


class ExplodingProgress:
    """Progress callback that always fails."""

    def __call__(self, snapshot: dict) -> None:
        raise RuntimeError("progress callback failure")


class TestTrainingLoopGuards:
    """Invalid configurations and defensive behaviours."""

    def test_no_trainable_parameter_is_rejected(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path / "data", name="train.bin", seed=11)
        config = tinyTrainingConfig(
            trainShards=[shard],
            checkpointDir=tmp_path / "checkpoints",
            numWorkers=0,
            dtype="fp32",
        )

        with pytest.raises(ValueError, match="aucun parametre"):
            TrainingLoop(config, FrozenRunner())  # type: ignore[arg-type]

    def test_snapshot_before_training(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=3)

        snapshot = loop.snapshot()

        assert snapshot["step"] == 0
        assert snapshot["epoch"] == 0
        assert snapshot["progress"] == 0.0
        assert snapshot["loss"] is None
        assert snapshot["bestValLoss"] is None
        assert snapshot["cancelled"] is False
        assert snapshot["learningRate"] > 0

    def test_progress_callback_failure_does_not_stop_training(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=2, progressCallback=ExplodingProgress())

        result = loop.train()

        assert result.steps == 2

    def test_evaluate_returns_none_when_eval_steps_is_zero(self, tmp_path: Path) -> None:
        valShard = writeTinyShard(tmp_path / "data", name="val.bin", seed=23)
        loop = buildLoop(tmp_path, valShards=[valShard], evalSteps=0)

        assert loop.evaluate() is None

    def test_checkpoint_without_validation_has_no_val_loss(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(tmp_path, checkpointRepo=repository, maxSteps=1)

        result = loop.train()

        latest = repository.findLatest()
        assert latest is not None
        assert latest.valLoss is None
        assert result.bestValLoss == result.finalLoss

    def test_best_val_loss_is_persisted_in_the_final_checkpoint(self, tmp_path: Path) -> None:
        valShard = writeTinyShard(tmp_path / "data", name="val.bin", seed=23)
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(
            tmp_path,
            valShards=[valShard],
            checkpointRepo=repository,
            maxSteps=2,
            evalInterval=1,
        )

        loop.train()

        latest = repository.findLatest()
        assert latest is not None
        assert latest.valLoss is not None
        assert latest.valLoss == pytest.approx(loop.bestValLoss)

    def test_checkpoint_id_is_prefixed_by_the_run_id(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(tmp_path, checkpointRepo=repository, maxSteps=1)

        loop.train()

        latest = repository.findLatest()
        assert latest is not None
        assert latest.id == "test-run:final"
        assert latest.metadata["runId"] == "test-run"

    def test_disabled_checkpoint_interval_keeps_only_the_final_file(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path / "index")
        loop = buildLoop(
            tmp_path,
            checkpointRepo=repository,
            maxSteps=3,
            checkpointInterval=0,
        )

        loop.train()

        assert repository.count() == 1
        assert (Path(loop.config.checkpointDir) / "checkpoint_final.pt").is_file()

    def test_disabled_log_interval_keeps_history_empty(self, tmp_path: Path) -> None:
        loop = buildLoop(tmp_path, maxSteps=2, logInterval=0)

        loop.train()

        assert loop.history == []
