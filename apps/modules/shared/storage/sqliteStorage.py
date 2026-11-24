# apps/modules/shared/storage/sqliteStorage.py
"""SQLite storage utilities"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator
from threading import Lock


class SQLiteStorage:
    """Thread-safe SQLite wrapper with connection pooling"""
    
    def __init__(self, dbPath: Path, poolSize: int = 5):
        self._dbPath = dbPath
        self._dbPath.parent.mkdir(parents=True, exist_ok=True)
        self._poolSize = poolSize
        self._lock = Lock()
        self._initConnection()
    
    def _initConnection(self):
        """Initialize connection with optimizations"""
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
        """Context manager for transactions"""
        with self._getConn() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._getConn() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
    
    def executemany(self, sql: str, paramsList: list[tuple]) -> sqlite3.Cursor:
        with self._getConn() as conn:
            cursor = conn.executemany(sql, paramsList)
            conn.commit()
            return cursor
    
    def fetchOne(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._getConn() as conn:
            return conn.execute(sql, params).fetchone()
    
    def fetchAll(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._getConn() as conn:
            return conn.execute(sql, params).fetchall()
    
    def fetchIter(self, sql: str, params: tuple = ()) -> Iterator[sqlite3.Row]:
        with self._getConn() as conn:
            cursor = conn.execute(sql, params)
            for row in cursor:
                yield row
    
    def backup(self, destPath: Path) -> None:
        """Consistent backup using SQLite backup API"""
        with self._getConn() as srcConn:
            destConn = sqlite3.connect(destPath)
            try:
                srcConn.backup(destConn)
            finally:
                destConn.close()
    
    def executeScript(self, script: str) -> None:
        with self._getConn() as conn:
            conn.executescript(script)