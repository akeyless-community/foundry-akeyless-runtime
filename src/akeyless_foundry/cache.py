"""In-memory TTL cache for secret values and auth tokens."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    value: T
    expires_at: float


class TtlCache(Generic[T]):
    def __init__(self) -> None:
        self._entries: dict[str, _CacheEntry[T]] = {}

    def get(self, key: str, now: float | None = None) -> T | None:
        now = time.monotonic() if now is None else now
        entry = self._entries.get(key)
        if entry is None:
            return None
        if now >= entry.expires_at:
            del self._entries[key]
            return None
        return entry.value

    def set(self, key: str, value: T, ttl_seconds: float, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        self._entries[key] = _CacheEntry(value=value, expires_at=now + ttl_seconds)

    def delete(self, key: str) -> None:
        self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()
