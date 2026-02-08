import time
import threading
from collections import defaultdict


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    """
    Simple thread-safe rate limiter.

    Allows `max_requests` per `window_seconds` per key.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str) -> None:
        now = time.time()

        with self._lock:
            window_start = now - self.window_seconds
            timestamps = self._requests[key]

            # Drop expired timestamps
            self._requests[key] = [
                t for t in timestamps if t > window_start
            ]

            if len(self._requests[key]) >= self.max_requests:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for key={key}"
                )

            self._requests[key].append(now)
