# apps/modules/model/repositories/checkpointRepository.py
"""Checkpoint repository - `.pt` files indexed in SQLite."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from apps.modules.shared.kernel.exceptions import ResourceNotFoundError
from apps.modules.shared.storage.sqliteStorage import SQLiteStorage

from ..models.modelModel import Checkpoint

INDEX_FILE_NAME = "checkpoints_index.sqlite"

CHECKPOINT_SCHEMA = """
CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    step INTEGER NOT NULL,
    epoch INTEGER NOT NULL,
    loss REAL NOT NULL,
    valLoss REAL,
    modelConfig TEXT NOT NULL,
    trainingConfig TEXT,
    createdAt TEXT NOT NULL,
    isBest INTEGER NOT NULL DEFAULT 0,
    modelName TEXT,
    metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_checkpoints_model ON checkpoints(modelName);
CREATE INDEX IF NOT EXISTS idx_checkpoints_step ON checkpoints(step);
"""

_UPSERT_SQL = """
INSERT INTO checkpoints (
    id, path, step, epoch, loss, valLoss, modelConfig,
    trainingConfig, createdAt, isBest, modelName, metadata
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    path = excluded.path,
    step = excluded.step,
    epoch = excluded.epoch,
    loss = excluded.loss,
    valLoss = excluded.valLoss,
    modelConfig = excluded.modelConfig,
    trainingConfig = excluded.trainingConfig,
    createdAt = excluded.createdAt,
    isBest = excluded.isBest,
    modelName = excluded.modelName,
    metadata = excluded.metadata
"""


class CheckpointRepository:
    """Persist training snapshots and query them by step, model or best loss."""

    def __init__(self, baseDir: Path) -> None:
        self._baseDir = baseDir
        self._baseDir.mkdir(parents=True, exist_ok=True)
        self._db = SQLiteStorage(self._baseDir / INDEX_FILE_NAME)
        self._db.executeScript(CHECKPOINT_SCHEMA)

    @property
    def baseDir(self) -> Path:
        """Directory holding checkpoint files and the SQLite index."""
        return self._baseDir

    def save(
        self,
        checkpoint: Checkpoint,
        state: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """Register a checkpoint, writing its `.pt` payload when provided."""
        if state is not None:
            checkpoint.path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(state, checkpoint.path)
        if checkpoint.isBest:
            self._db.execute(
                "UPDATE checkpoints SET isBest = 0 WHERE modelName IS ? AND id != ?",
                (checkpoint.modelName, checkpoint.id),
            )
        self._db.execute(
            _UPSERT_SQL,
            (
                checkpoint.id,
                str(checkpoint.path),
                checkpoint.step,
                checkpoint.epoch,
                checkpoint.loss,
                checkpoint.valLoss,
                json.dumps(checkpoint.modelConfig.toDict(), ensure_ascii=False),
                (
                    json.dumps(checkpoint.trainingConfig.toDict(), ensure_ascii=False)
                    if checkpoint.trainingConfig
                    else None
                ),
                checkpoint.createdAt.isoformat(),
                1 if checkpoint.isBest else 0,
                checkpoint.modelName,
                json.dumps(checkpoint.metadata, ensure_ascii=False),
            ),
        )
        return checkpoint

    def findById(self, checkpointId: str) -> Checkpoint | None:
        """Return a checkpoint by identifier, or None when unknown."""
        row = self._db.fetchOne(
            "SELECT * FROM checkpoints WHERE id = ?",
            (checkpointId,),
        )
        return self._rowToCheckpoint(row) if row is not None else None

    def requireById(self, checkpointId: str) -> Checkpoint:
        """Return a checkpoint or raise `ResourceNotFoundError`."""
        checkpoint = self.findById(checkpointId)
        if checkpoint is None:
            raise ResourceNotFoundError(
                "Checkpoint introuvable",
                details={"checkpointId": checkpointId},
            )
        return checkpoint

    def findLatest(self, modelName: str | None = None) -> Checkpoint | None:
        """Return the most advanced checkpoint (optionally for one model)."""
        if modelName is None:
            row = self._db.fetchOne(
                "SELECT * FROM checkpoints ORDER BY step DESC, createdAt DESC LIMIT 1"
            )
        else:
            row = self._db.fetchOne(
                "SELECT * FROM checkpoints WHERE modelName = ? "
                "ORDER BY step DESC, createdAt DESC LIMIT 1",
                (modelName,),
            )
        return self._rowToCheckpoint(row) if row is not None else None

    def findBest(self, modelName: str | None = None) -> Checkpoint | None:
        """Return the checkpoint flagged as best (lowest validation loss)."""
        if modelName is None:
            row = self._db.fetchOne(
                "SELECT * FROM checkpoints WHERE isBest = 1 "
                "ORDER BY step DESC LIMIT 1"
            )
        else:
            row = self._db.fetchOne(
                "SELECT * FROM checkpoints WHERE isBest = 1 AND modelName = ? "
                "ORDER BY step DESC LIMIT 1",
                (modelName,),
            )
        return self._rowToCheckpoint(row) if row is not None else None

    def listAll(
        self,
        limit: int = 50,
        offset: int = 0,
        modelName: str | None = None,
    ) -> list[Checkpoint]:
        """Return checkpoints ordered from the most advanced to the oldest."""
        if limit <= 0:
            return []
        if modelName is None:
            rows = self._db.fetchAll(
                "SELECT * FROM checkpoints ORDER BY step DESC, createdAt DESC "
                "LIMIT ? OFFSET ?",
                (limit, max(0, offset)),
            )
        else:
            rows = self._db.fetchAll(
                "SELECT * FROM checkpoints WHERE modelName = ? "
                "ORDER BY step DESC, createdAt DESC LIMIT ? OFFSET ?",
                (modelName, limit, max(0, offset)),
            )
        return [self._rowToCheckpoint(row) for row in rows]

    def count(self, modelName: str | None = None) -> int:
        """Count indexed checkpoints."""
        if modelName is None:
            row = self._db.fetchOne("SELECT COUNT(*) AS total FROM checkpoints")
        else:
            row = self._db.fetchOne(
                "SELECT COUNT(*) AS total FROM checkpoints WHERE modelName = ?",
                (modelName,),
            )
        return int(row["total"]) if row is not None else 0

    def pruneOld(
        self,
        keepLastN: int = 3,
        modelName: str | None = None,
        protectBest: bool = True,
    ) -> int:
        """Delete the oldest checkpoints beyond `keepLastN` and return the count.

        The checkpoint flagged as best is never pruned unless `protectBest` is
        disabled, so inference always keeps a usable model.
        """
        if keepLastN < 0:
            raise ValueError("keepLastN must be >= 0")
        keepIds = [
            checkpoint.id
            for checkpoint in self.listAll(limit=keepLastN, modelName=modelName)
        ]
        if protectBest:
            best = self.findBest(modelName=modelName)
            if best is not None:
                keepIds.append(best.id)
        if modelName is None:
            rows = self._db.fetchAll("SELECT id FROM checkpoints")
        else:
            rows = self._db.fetchAll(
                "SELECT id FROM checkpoints WHERE modelName = ?",
                (modelName,),
            )
        keep = set(keepIds)
        removed = 0
        for row in rows:
            checkpointId = str(row["id"])
            if checkpointId in keep:
                continue
            self.delete(checkpointId)
            removed += 1
        return removed

    def delete(self, checkpointId: str) -> bool:
        """Delete a checkpoint row and its `.pt` file when inside the base dir."""
        checkpoint = self.findById(checkpointId)
        if checkpoint is None:
            return False
        self._removeFile(checkpoint.path)
        self._db.execute("DELETE FROM checkpoints WHERE id = ?", (checkpointId,))
        return True

    def _removeFile(self, path: Path) -> None:
        """Remove a checkpoint file only when it lives inside the base dir."""
        resolved = path.resolve()
        if not resolved.is_relative_to(self._baseDir.resolve()):
            return
        if resolved.is_file():
            resolved.unlink()

    @staticmethod
    def _rowToCheckpoint(row: Any) -> Checkpoint:
        """Map a SQLite row to a domain `Checkpoint`."""
        createdAt = datetime.fromisoformat(row["createdAt"])
        if createdAt.tzinfo is None:
            createdAt = createdAt.replace(tzinfo=timezone.utc)
        payload = {
            "id": row["id"],
            "path": row["path"],
            "step": row["step"],
            "epoch": row["epoch"],
            "loss": row["loss"],
            "valLoss": row["valLoss"],
            "modelConfig": json.loads(row["modelConfig"]),
            "trainingConfig": (
                json.loads(row["trainingConfig"]) if row["trainingConfig"] else None
            ),
            "createdAt": createdAt.isoformat(),
            "isBest": bool(row["isBest"]),
            "modelName": row["modelName"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        }
        return Checkpoint.fromDict(payload)
