"""Chaining hash table. Package id in, package record out."""

from __future__ import annotations

from collections.abc import Hashable, Iterator
from typing import Generic, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

# Knuth's multiplicative constant spreads consecutive ids across buckets.
_MULTIPLIER = 2_654_435_761
_MAX_LOAD = 0.75


class ChainingHashTable(Generic[K, V]):
    """Hash map with separate chaining and automatic growth.

    Each bucket is a list of (key, value) pairs. A collision appends to the
    bucket, and the table doubles once the load factor passes 0.75, which
    keeps chains short and every operation O(1) on average.
    """

    def __init__(self, initial_capacity: int = 16) -> None:
        if initial_capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._size = 0
        self._buckets: list[list[tuple[K, V]]] = [[] for _ in range(initial_capacity)]

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        bucket = self._buckets[self._index(key)]
        return any(existing == key for existing, _ in bucket)

    def __iter__(self) -> Iterator[K]:
        for bucket in self._buckets:
            for key, _ in bucket:
                yield key

    @property
    def capacity(self) -> int:
        """Current bucket count."""
        return len(self._buckets)

    def _index(self, key: object) -> int:
        return (hash(key) * _MULTIPLIER) % len(self._buckets)

    def insert(self, key: K, value: V) -> None:
        """Insert or replace. Average O(1). Grows the table past 75% load."""
        bucket = self._buckets[self._index(key)]
        for i, (existing, _) in enumerate(bucket):
            if existing == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1
        if self._size / len(self._buckets) > _MAX_LOAD:
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
        """Every stored value, in bucket order. O(n)."""
        return [value for bucket in self._buckets for _, value in bucket]

    def _resize(self) -> None:
        """Double the bucket count and rehash. O(n), rare enough to keep insert O(1)."""
        old = self._buckets
        self._buckets = [[] for _ in range(len(old) * 2)]
        for bucket in old:
            for key, value in bucket:
                self._buckets[self._index(key)].append((key, value))
