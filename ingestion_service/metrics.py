import time
from collections import defaultdict
from contextlib import contextmanager

class MetricsRegistry:
    """
    In-memory metrics registry.
    """
    def __init__(self):
        self.counters = defaultdict(int)
        self.timings = defaultdict(list)

    def incr(self, name:str ,value: int = 1):
        self.counters[name] += value

    def record_time(self, name:str, duration: float):
        self.timings[name].append(duration)

    @contextmanager
    def timer(self,name:str):
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.record_time(name,duration)


metrics = MetricsRegistry()
