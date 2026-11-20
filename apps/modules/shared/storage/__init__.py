# apps/modules/shared/storage/__init__.py
"""Local storage utilities only"""

from .fileStorage import FileStorage
from .sqliteStorage import SQLiteStorage

__all__ = ["FileStorage", "SQLiteStorage"]