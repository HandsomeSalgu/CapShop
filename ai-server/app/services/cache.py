import copy
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Hashable


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float
    created_at: float


class TtlCache:
    def __init__(self) -> None:
        self._items: dict[Hashable, _CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: Hashable) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None

            if entry.expires_at <= now:
                self._items.pop(key, None)
                return None

            return copy.deepcopy(entry.value)

    def set(self, key: Hashable, value: Any, *, ttl_seconds: int, max_size: int) -> None:
        if ttl_seconds <= 0 or max_size <= 0:
            return

        now = time.monotonic()
        with self._lock:
            self._remove_expired(now)
            self._items[key] = _CacheEntry(
                value=copy.deepcopy(value),
                expires_at=now + ttl_seconds,
                created_at=now,
            )
            self._trim_to_size(max_size)

    def _remove_expired(self, now: float) -> None:
        expired_keys = [
            key
            for key, entry in self._items.items()
            if entry.expires_at <= now
        ]
        for key in expired_keys:
            self._items.pop(key, None)

    def _trim_to_size(self, max_size: int) -> None:
        overflow = len(self._items) - max_size
        if overflow <= 0:
            return

        oldest_keys = sorted(
            self._items,
            key=lambda key: self._items[key].created_at,
        )[:overflow]
        for key in oldest_keys:
            self._items.pop(key, None)


search_cache = TtlCache()
