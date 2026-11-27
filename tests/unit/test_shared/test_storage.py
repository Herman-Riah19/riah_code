# tests/unit/test_shared/test_storage.py
"""Tests for the shared file and SQLite storage helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from apps.modules.shared.storage.fileStorage import FileStorage
from apps.modules.shared.storage.sqliteStorage import SQLiteStorage


@pytest.fixture
def storage(tmp_path: Path) -> FileStorage:
    """File storage rooted in a temporary directory."""
    return FileStorage(tmp_path)


class TestFileStorageJsonl:
    """Streaming JSONL read/write, compressed or not."""

    @pytest.mark.parametrize("compress", [True, False])
    def test_round_trip(self, storage: FileStorage, tmp_path: Path, compress: bool) -> None:
        path = tmp_path / "docs" / "data.jsonl.gz"

        with storage.writeJsonl(path, compress=compress) as writeLine:
            writeLine({"id": 1})
            writeLine({"id": 2})

        assert list(storage.readJsonl(path, compress=compress)) == [{"id": 1}, {"id": 2}]

    def test_append_keeps_previous_lines(self, storage: FileStorage, tmp_path: Path) -> None:
        path = tmp_path / "data.jsonl.gz"

        with storage.writeJsonl(path, append=True) as writeLine:
            writeLine({"id": 1})
        with storage.writeJsonl(path, append=True) as writeLine:
            writeLine({"id": 2})

        assert [record["id"] for record in storage.readJsonl(path)] == [1, 2]

    def test_blank_lines_are_skipped(self, storage: FileStorage, tmp_path: Path) -> None:
        path = tmp_path / "data.jsonl"
        path.write_text('{"id": 1}\n\n{"id": 2}\n', encoding="utf-8")

        assert [record["id"] for record in storage.readJsonl(path, compress=False)] == [1, 2]

    def test_read_missing_file_raises(self, storage: FileStorage, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            list(storage.readJsonl(tmp_path / "missing.jsonl"))


class TestFileStorageFiles:
    """JSON documents and filesystem helpers."""

    def test_json_round_trip(self, storage: FileStorage, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "config.json"

        storage.writeJson(path, {"dim": 64})
        assert storage.readJson(path) == {"dim": 64}

    def test_copy_move_delete_and_list(self, storage: FileStorage, tmp_path: Path) -> None:
        source = tmp_path / "a.txt"
        source.write_text("payload", encoding="utf-8")
        copied = tmp_path / "b.txt"
        moved = tmp_path / "c.txt"

        storage.copy(source, copied)
        assert copied.read_text(encoding="utf-8") == "payload"

        storage.move(copied, moved)
        assert not copied.exists()
        assert moved.exists()

        storage.delete(moved)
        assert not moved.exists()

        assert [path.name for path in storage.listFiles("*.txt")] == ["a.txt"]

    def test_delete_missing_is_a_noop(self, storage: FileStorage, tmp_path: Path) -> None:
        storage.delete(tmp_path / "missing")

    def test_get_size(self, storage: FileStorage, tmp_path: Path) -> None:
        path = tmp_path / "size.txt"
        path.write_text("12345", encoding="utf-8")

        assert storage.getSize(path) == 5
        assert storage.getSize(tmp_path / "missing") == 0


class TestSQLiteStorage:
    """SQLite execution, transactions and backup."""

    @pytest.fixture
    def db(self, tmp_path: Path) -> SQLiteStorage:
        database = SQLiteStorage(tmp_path / "db" / "index.sqlite")
        database.executeScript("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        return database

    def test_execute_and_fetch(self, db: SQLiteStorage) -> None:
        db.execute("INSERT INTO items (name) VALUES (?)", ("alpha",))

        row = db.fetchOne("SELECT name FROM items WHERE id = ?", (1,))
        assert row is not None
        assert row["name"] == "alpha"

    def test_fetch_one_returns_none_when_empty(self, db: SQLiteStorage) -> None:
        assert db.fetchOne("SELECT * FROM items") is None

    def test_executemany_and_fetch_all(self, db: SQLiteStorage) -> None:
        db.executemany("INSERT INTO items (name) VALUES (?)", [("a",), ("b",)])

        assert [row["name"] for row in db.fetchAll("SELECT name FROM items ORDER BY id")] == [
            "a",
            "b",
        ]

    def test_fetch_iter_streams_rows(self, db: SQLiteStorage) -> None:
        db.executemany("INSERT INTO items (name) VALUES (?)", [("a",), ("b",)])

        assert [row["name"] for row in db.fetchIter("SELECT name FROM items ORDER BY id")] == [
            "a",
            "b",
        ]

    def test_transaction_commits(self, db: SQLiteStorage) -> None:
        with db.transaction() as conn:
            conn.execute("INSERT INTO items (name) VALUES (?)", ("kept",))

        assert db.fetchOne("SELECT name FROM items")["name"] == "kept"

    def test_transaction_rolls_back_on_error(self, db: SQLiteStorage) -> None:
        with pytest.raises(sqlite3.IntegrityError), db.transaction() as conn:
            conn.execute("INSERT INTO items (id, name) VALUES (1, 'a')")
            conn.execute("INSERT INTO items (id, name) VALUES (1, 'b')")

        assert db.fetchOne("SELECT * FROM items") is None

    def test_backup_produces_a_readable_copy(self, db: SQLiteStorage, tmp_path: Path) -> None:
        db.execute("INSERT INTO items (name) VALUES (?)", ("backed",))
        destination = tmp_path / "backup.sqlite"

        db.backup(destination)

        with sqlite3.connect(destination) as conn:
            assert conn.execute("SELECT name FROM items").fetchone()[0] == "backed"
