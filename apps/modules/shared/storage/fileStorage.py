# apps/modules/shared/storage/fileStorage.py
"""File system storage utilities"""
import json
import gzip
import shutil
from pathlib import Path
from typing import Iterator, Any
from contextlib import contextmanager


class FileStorage:
    """Local file system storage with JSONL/Parquet support"""
    
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
        self._baseDir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def writeJsonl(self, filePath: Path, compress: bool = True):
        """Context manager for writing JSONL (optionally gzipped)"""
        filePath.parent.mkdir(parents=True, exist_ok=True)
        mode = "wt"
        opener = gzip.open if compress else open
        with opener(filePath, mode, encoding="utf-8") as f:
            def writeLine(obj: dict):
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            yield writeLine
    
    def readJsonl(self, filePath: Path, compress: bool = True) -> Iterator[dict]:
        """Read JSONL line by line (streaming)"""
        opener = gzip.open if compress else open
        with opener(filePath, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    
    def writeJson(self, filePath: Path, data: Any, indent: int = 2) -> None:
        filePath.parent.mkdir(parents=True, exist_ok=True)
        filePath.write_text(json.dumps(data, ensure_ascii=False, indent=indent))
    
    def readJson(self, filePath: Path) -> Any:
        return json.loads(filePath.read_text())
    
    def copy(self, src: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    
    def move(self, src: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    
    def delete(self, path: Path) -> None:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    
    def listFiles(self, pattern: str = "*") -> list[Path]:
        return list(self._baseDir.glob(pattern))
    
    def getSize(self, path: Path) -> int:
        return path.stat().st_size if path.exists() else 0