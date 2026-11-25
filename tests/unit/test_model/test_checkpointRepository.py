# tests/unit/test_model/test_checkpointRepository.py
"""Tests for the SQLite-backed checkpoint repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from apps.modules.model.models.modelModel import Checkpoint
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.shared.kernel.exceptions import ResourceNotFoundError

from tinyModel import tinyModelConfig, tinyTrainingConfig


def _checkpoint(
    baseDir: Path,
    checkpointId: str,
    step: int,
    *,
    isBest: bool = False,
    modelName: str | None = None,
    valLoss: float | None = None,
) -> Checkpoint:
    """Build a checkpoint whose file lives inside `baseDir`."""
    return Checkpoint(
        id=checkpointId,
        path=baseDir / f"{checkpointId}.pt",
        step=step,
        epoch=step // 10,
        loss=2.0 / max(step, 1),
        valLoss=valLoss,
        modelConfig=tinyModelConfig(),
        trainingConfig=tinyTrainingConfig(),
        createdAt=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=step),
        isBest=isBest,
        modelName=modelName,
        metadata={"tag": checkpointId},
    )


class TestCheckpointSave:
    """Registration and lookup."""

    def test_save_writes_payload_and_index(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        checkpoint = _checkpoint(tmp_path, "ckpt-1", 10)

        repository.save(checkpoint, state={"model": {}})

        assert checkpoint.path.is_file()
        restored = repository.findById("ckpt-1")
        assert restored == checkpoint

    def test_save_without_state_skips_file(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        checkpoint = _checkpoint(tmp_path, "ckpt-2", 5)

        repository.save(checkpoint)

        assert not checkpoint.path.exists()
        assert repository.findById("ckpt-2") is not None

    def test_unknown_id_returns_none(self, tmp_path: Path) -> None:
        assert CheckpointRepository(tmp_path).findById("missing") is None

    def test_require_by_id_raises(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        with pytest.raises(ResourceNotFoundError):
            repository.requireById("missing")


class TestCheckpointQueries:
    """Ordering, best selection and pagination."""

    def test_find_latest_uses_highest_step(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        for step in (10, 30, 20):
            repository.save(_checkpoint(tmp_path, f"ckpt-{step}", step))

        latest = repository.findLatest()

        assert latest is not None
        assert latest.step == 30

    def test_find_latest_filters_by_model_name(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        repository.save(_checkpoint(tmp_path, "a", 10, modelName="alpha"))
        repository.save(_checkpoint(tmp_path, "b", 50, modelName="beta"))

        latest = repository.findLatest(modelName="alpha")

        assert latest is not None
        assert latest.id == "a"

    def test_new_best_clears_previous_best(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        first = _checkpoint(tmp_path, "first", 10, isBest=True, modelName="m")
        second = _checkpoint(tmp_path, "second", 20, isBest=True, modelName="m")

        repository.save(first)
        repository.save(second)

        best = repository.findBest(modelName="m")
        assert best is not None
        assert best.id == "second"
        assert repository.findById("first").isBest is False

    def test_best_is_scoped_per_model_name(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        repository.save(_checkpoint(tmp_path, "a", 10, isBest=True, modelName="alpha"))
        repository.save(_checkpoint(tmp_path, "b", 20, isBest=True, modelName="beta"))

        assert repository.findBest(modelName="alpha").id == "a"
        assert repository.findBest(modelName="beta").id == "b"

    def test_list_all_orders_and_paginates(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        for step in range(1, 6):
            repository.save(_checkpoint(tmp_path, f"ckpt-{step}", step))

        everything = repository.listAll()
        firstPage = repository.listAll(limit=2)

        assert [checkpoint.step for checkpoint in everything] == [5, 4, 3, 2, 1]
        assert [checkpoint.step for checkpoint in firstPage] == [5, 4]
        assert repository.listAll(limit=0) == []

    def test_count(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        repository.save(_checkpoint(tmp_path, "a", 1, modelName="alpha"))
        repository.save(_checkpoint(tmp_path, "b", 2, modelName="beta"))

        assert repository.count() == 2
        assert repository.count(modelName="alpha") == 1


class TestCheckpointDeletion:
    """Pruning and file cleanup."""

    def test_prune_old_removes_files_and_rows(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        for step in range(1, 5):
            repository.save(_checkpoint(tmp_path, f"ckpt-{step}", step), state={"model": {}})

        removed = repository.pruneOld(keepLastN=2)

        assert removed == 2
        assert repository.count() == 2
        assert not (tmp_path / "ckpt-1.pt").exists()
        assert not (tmp_path / "ckpt-2.pt").exists()
        assert (tmp_path / "ckpt-3.pt").exists()
        assert (tmp_path / "ckpt-4.pt").exists()

    def test_prune_rejects_negative_keep(self, tmp_path: Path) -> None:
        repository = CheckpointRepository(tmp_path)
        with pytest.raises(ValueError, match="keepLastN"):
            repository.pruneOld(keepLastN=-1)

    def test_delete_missing_returns_false(self, tmp_path: Path) -> None:
        assert CheckpointRepository(tmp_path).delete("missing") is False

    def test_delete_keeps_files_outside_base_dir(self, tmp_path: Path) -> None:
        repositoryDir = tmp_path / "index"
        outsidePath = tmp_path / "outside.pt"
        repository = CheckpointRepository(repositoryDir)
        checkpoint = Checkpoint(
            id="outside",
            path=outsidePath,
            step=1,
            epoch=0,
            loss=1.0,
            modelConfig=tinyModelConfig(),
            createdAt=datetime.now(timezone.utc),
        )
        repository.save(checkpoint, state={"model": {}})

        assert repository.delete("outside") is True
        assert outsidePath.is_file()
        assert repository.findById("outside") is None
