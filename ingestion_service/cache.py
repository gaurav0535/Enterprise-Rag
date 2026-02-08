import time
from collections import OrderedDict
from typing import Generic, TypeVar, Optional

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """
    LRU Cache with TTL (Time-To-Live) support.

    Guarantees:
    - O(1) get/set
    - Deterministic eviction
    - TTL-based expiry
    """

    def __init__(self, capacity: int = 128, ttl_seconds: int | None = None):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")

        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[K, tuple[V, float]] = OrderedDict()

    def _is_expired(self, timestamp: float) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - timestamp) > self.ttl_seconds

    def get(self, key: K) -> Optional[V]:
        if key not in self._store:
            return None

        value, ts = self._store[key]

        if self._is_expired(ts):
            # Expired → hard delete
            del self._store[key]
            return None

        # Mark as recently used
        self._store.move_to_end(key)
        return value

    def set(self, key: K, value: V) -> None:
        now = time.time()

        if key in self._store:
            self._store.move_to_end(key)

        self._store[key] = (value, now)

        # Evict LRU if needed
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def invalidate(self, key: K) -> None:
        """Remove a specific cache entry."""
        self._store.pop(key, None)

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        self._store.clear()

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)
