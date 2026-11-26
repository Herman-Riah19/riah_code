# tests/unit/test_model/test_lruCache.py
"""Tests for the bounded LRU cache used by the inference service."""

from __future__ import annotations

import pytest

from apps.modules.shared.kernel.lruCache import LRUCache


class TestLRUCapacity:
    """Capacity validation and eviction order."""

    def test_capacity_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="capacity"):
            LRUCache(capacity=0)

    def test_capacity_property(self) -> None:
        assert LRUCache[str, int](capacity=3).capacity == 3

    def test_put_beyond_capacity_evicts_the_oldest(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)

        assert cache.put("a", 1) is None
        assert cache.put("b", 2) is None
        assert cache.put("c", 3) == 1
        assert cache.keys() == ["b", "c"]
        assert len(cache) == 2

    def test_get_marks_the_entry_as_recent(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)

        assert cache.get("a") == 1
        assert cache.put("c", 3) == 2  # "b" is now the least recent.
        assert cache.keys() == ["a", "c"]

    def test_put_existing_key_refreshes_recency(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)

        cache.put("a", 10)
        assert cache.put("c", 3) == 2
        assert cache.get("a") == 10
        assert "b" not in cache

    def test_storing_the_same_key_does_not_evict(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=1)
        cache.put("a", 1)
        assert cache.put("a", 2) is None
        assert cache.get("a") == 2
        assert len(cache) == 1


class TestLruAccessors:
    """Lookups, membership and removal helpers."""

    def test_missing_key_returns_none(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)
        assert cache.get("missing") is None

    def test_require_returns_the_value(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)
        cache.put("a", 1)

        assert cache.require("a") == 1

    def test_require_raises_for_unknown_key(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)

        with pytest.raises(KeyError):
            cache.require("missing")

    def test_contains_does_not_touch_recency(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)

        assert "a" in cache
        assert cache.put("c", 3) == 1
        assert cache.keys() == ["b", "c"]

    def test_pop_removes_and_returns_the_value(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=2)
        cache.put("a", 1)

        assert cache.pop("a") == 1
        assert cache.pop("a") is None
        assert len(cache) == 0

    def test_clear_drops_every_entry(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=3)
        cache.put("a", 1)
        cache.put("b", 2)

        cache.clear()

        assert len(cache) == 0
        assert cache.keys() == []

    def test_iteration_follows_lru_order(self) -> None:
        cache: LRUCache[str, int] = LRUCache(capacity=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.get("a")

        assert list(cache) == ["b", "c", "a"]
