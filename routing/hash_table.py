"""Chaining hash table. Package id in, package record out."""

from __future__ import annotations

from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")

# Fixed mix so the same id always lands in the same bucket.
_MULTIPLIER = 2_654_435_761
_MAX_LOAD = 0.75


class ChainingHashTable:
    """Hash map with separate chaining and automatic growth."""

    def __init__(self, initial_capacity: int = 16) -> None:
        if initial_capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._size = 0
        self._buckets: list[list[tuple[K, V]]] = [[] for _ in range(initial_capacity)]
        self._resizing = False

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: K) -> bool:
        return self.lookup(key) is not None

    def _index(self, key: K) -> int:
        return (int(key) * _MULTIPLIER) % len(self._buckets)

    def insert(self, key: K, value: V) -> None:
        """Insert or replace. Average O(1). Grows the table past 75% load."""
        bucket = self._buckets[self._index(key)]
        for i, (existing, _) in enumerate(bucket):
            if existing == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1
        if not self._resizing and self._size / len(self._buckets) > _MAX_LOAD:
            self._resize()

    def lookup(self, key: K) -> V | None:
        """Return the value for key, or None. Average O(1)."""
        for existing, value in self._buckets[self._index(key)]:
            if existing == key:
                return value
        return None

    def remove(self, key: K) -> bool:
        """Remove key. Average O(1). Returns whether it was present."""
        bucket = self._buckets[self._index(key)]
        for i, (existing, _) in enumerate(bucket):
            if existing == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def values(self) -> list[V]:
        """Every stored value. O(n)."""
        return [value for bucket in self._buckets for _, value in bucket]

    def _resize(self) -> None:
        """Double the bucket count and rehash. O(n), rare enough to keep insert O(1)."""
        old = self._buckets
        self._resizing = True
        try:
            self._buckets = [[] for _ in range(len(old) * 2)]
            self._size = 0
            for bucket in old:
                for key, value in bucket:
                    self.insert(key, value)
        finally:
            self._resizing = False
