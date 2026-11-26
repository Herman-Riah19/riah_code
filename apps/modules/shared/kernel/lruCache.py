# apps/modules/shared/kernel/lruCache.py
"""Small thread-safe LRU cache used for loaded models and other heavy objects."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from threading import RLock
from typing import Generic, TypeVar

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


class LRUCache(Generic[KeyType, ValueType]):
    """Bounded least-recently-used mapping with explicit eviction."""

    def __init__(self, capacity: int = 2) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._items: OrderedDict[KeyType, ValueType] = OrderedDict()
        self._lock = RLock()

    @property
    def capacity(self) -> int:
        """Maximum number of cached entries."""
        return self._capacity

    def __len__(self) -> int:
        """Number of cached entries."""
        with self._lock:
            return len(self._items)

    def __contains__(self, key: object) -> bool:
        """Return True when the key is cached (without touching its recency)."""
        with self._lock:
            return key in self._items

    def __iter__(self) -> Iterator[KeyType]:
        """Iterate over cached keys, from the least to the most recently used."""
        with self._lock:
            return iter(list(self._items))

    def keys(self) -> list[KeyType]:
        """Return the cached keys, from the least to the most recently used."""
        with self._lock:
            return list(self._items)

    def get(self, key: KeyType) -> ValueType | None:
        """Return the cached value and mark it as most recently used."""
        with self._lock:
            value = self._items.get(key)
            if value is None:
                return None
            self._items.move_to_end(key)
            return value

    def require(self, key: KeyType) -> ValueType:
        """Return the cached value or raise `KeyError`."""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def put(self, key: KeyType, value: ValueType) -> ValueType | None:
        """Store a value, returning the evicted value when capacity is exceeded."""
        with self._lock:
            if key in self._items:
                self._items.move_to_end(key)
            self._items[key] = value
            if len(self._items) <= self._capacity:
                return None
            _, evicted = self._items.popitem(last=False)
            return evicted

    def pop(self, key: KeyType) -> ValueType | None:
        """Remove and return a cached value, or None when absent."""
        with self._lock:
            return self._items.pop(key, None)

    def clear(self) -> None:
        """Drop every cached entry."""
        with self._lock:
            self._items.clear()
