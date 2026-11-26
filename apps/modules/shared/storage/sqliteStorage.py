# apps/modules/shared/storage/sqliteStorage.py
"""SQLite storage utilities."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, cast


class SQLiteStorage:
    """Thread-safe SQLite wrapper with one connection per operation."""

    def __init__(self, dbPath: Path, poolSize: int = 5) -> None:
        self._dbPath = dbPath
        self._dbPath.parent.mkdir(parents=True, exist_ok=True)
        self._poolSize = poolSize
        self._lock = Lock()
        self._initConnection()

    def _initConnection(self) -> None:
        """Apply connection pragmas used by the whole application."""
        with self._getConn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-32768")  # 32MB
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB

    @contextmanager
    def _getConn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            self._dbPath,
            check_same_thread=False,
            timeout=30.0,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a block inside one transaction."""
        with self._getConn() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        """Execute one statement and commit."""
        with self._getConn() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor

    def executemany(self, sql: str, paramsList: Sequence[Sequence[Any]]) -> sqlite3.Cursor:
        """Execute one statement for many parameter sets and commit."""
        with self._getConn() as conn:
            cursor = conn.executemany(sql, paramsList)
            conn.commit()
            return cursor

    def fetchOne(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
        """Return the first row of a query, or None."""
        with self._getConn() as conn:
            return cast("sqlite3.Row | None", conn.execute(sql, params).fetchone())

    def fetchAll(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        """Return every row of a query."""
        with self._getConn() as conn:
            return list(conn.execute(sql, params).fetchall())

    def fetchIter(self, sql: str, params: Sequence[Any] = ()) -> Iterator[sqlite3.Row]:
        """Stream the rows of a query."""
        with self._getConn() as conn:
            yield from conn.execute(sql, params)

    def backup(self, destPath: Path) -> None:
        """Create a consistent copy using the SQLite backup API."""
        with self._getConn() as srcConn:
            destConn = sqlite3.connect(destPath)
            try:
                srcConn.backup(destConn)
            finally:
                destConn.close()

    def executeScript(self, script: str) -> None:
        """Execute a multi-statement SQL script."""
        with self._getConn() as conn:
            conn.executescript(script)
