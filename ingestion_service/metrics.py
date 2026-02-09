# ingestion_service/metrics.py

import time
import threading
from collections import defaultdict, deque

class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.counters = defaultdict(int)
        self.timings = defaultdict(deque)

    # -------- Counters --------
    def incr(self, name: str, value: int = 1):
        with self._lock:
            self.counters[name] += value

    def get_counter(self, name: str) -> int:
        return self.counters.get(name, 0)

    # -------- Timings --------
    def timing(self, name: str, value_ms: float):
        with self._lock:
            self.timings[name].append(value_ms)
            # keep bounded memory
            if len(self.timings[name]) > 1000:
                self.timings[name].popleft()

    def stats(self, name: str):
        values = list(self.timings.get(name, []))
        if not values:
            return None

        values.sort()
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "p95": values[int(0.95 * len(values)) - 1],
            "max": max(values),
        }

    def snapshot(self):
        return {
            "counters": dict(self.counters),
            "timings": {k: self.stats(k) for k in self.timings},
        }


metrics = Metrics()
