# apps/modules/shared/storage/fileStorage.py
"""File system storage utilities."""

from __future__ import annotations

import gzip
import json
import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any, cast

JsonLineWriter = Callable[[dict[str, Any]], None]


class FileStorage:
    """Local file system storage with JSONL support."""

    def __init__(self, baseDir: Path) -> None:
        self._baseDir = baseDir
        self._baseDir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def writeJsonl(
        self,
        filePath: Path,
        compress: bool = True,
        append: bool = False,
    ) -> Iterator[JsonLineWriter]:
        """Yield a line writer for an optional gzip-compressed JSONL file."""
        filePath.parent.mkdir(parents=True, exist_ok=True)
        mode = ("at" if compress else "a") if append else ("wt" if compress else "w")

        if compress:
            with gzip.open(filePath, mode, encoding="utf-8") as gzipHandle:
                yield self._lineWriter(cast("IO[str]", gzipHandle))
            return

        with filePath.open(mode, encoding="utf-8") as textHandle:
            yield self._lineWriter(textHandle)

    def readJsonl(self, filePath: Path, compress: bool = True) -> Iterator[dict[str, Any]]:
        """Read JSONL line by line (streaming)."""
        if compress:
            with gzip.open(filePath, "rt", encoding="utf-8") as gzipHandle:
                yield from self._parseLines(cast("IO[str]", gzipHandle))
            return

        with filePath.open("r", encoding="utf-8") as textHandle:
            yield from self._parseLines(textHandle)

    @staticmethod
    def _lineWriter(handle: IO[str]) -> JsonLineWriter:
        """Build a writer writing one JSON object per line."""

        def writeLine(obj: dict[str, Any]) -> None:
            handle.write(json.dumps(obj, ensure_ascii=False) + "\n")

        return writeLine

    @staticmethod
    def _parseLines(handle: IO[str]) -> Iterator[dict[str, Any]]:
        """Decode non-empty lines of an open JSONL handle."""
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)

    def writeJson(self, filePath: Path, data: Any, indent: int = 2) -> None:
        """Write one JSON document."""
        filePath.parent.mkdir(parents=True, exist_ok=True)
        filePath.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")

    def readJson(self, filePath: Path) -> Any:
        """Read and decode one JSON document."""
        return json.loads(filePath.read_text(encoding="utf-8"))

    def copy(self, src: Path, dest: Path) -> None:
        """Copy a file, creating parent directories as needed."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    def move(self, src: Path, dest: Path) -> None:
        """Move a file, creating parent directories as needed."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))

    def delete(self, path: Path) -> None:
        """Delete a file or a directory tree when it exists."""
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)

    def listFiles(self, pattern: str = "*") -> list[Path]:
        """List files matching a glob pattern under the base directory."""
        return list(self._baseDir.glob(pattern))

    def getSize(self, path: Path) -> int:
        """Return the file size in bytes, or 0 when it does not exist."""
        return path.stat().st_size if path.exists() else 0
