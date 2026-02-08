import time
import threading
from collections import OrderedDict
from typing import Generic, TypeVar, Optional

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """
    Thread-safe LRU cache with TTL.

    Guarantees:
    - Safe under concurrent reads/writes
    - TTL expiry
    - Deterministic eviction
    """

    def __init__(self, capacity: int = 128, ttl_seconds: int | None = None):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")

        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[K, tuple[V, float]] = OrderedDict()
        self._lock = threading.Lock()

    def _is_expired(self, timestamp: float) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - timestamp) > self.ttl_seconds

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            if key not in self._store:
                return None

            value, ts = self._store[key]

            if self._is_expired(ts):
                del self._store[key]
                return None

            self._store.move_to_end(key)
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            now = time.time()

            if key in self._store:
                self._store.move_to_end(key)

            self._store[key] = (value, now)

            if len(self._store) > self.capacity:
                self._store.popitem(last=False)

    def invalidate(self, key: K) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_all(self) -> None:
        with self._lock:
            self._store.clear()

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
