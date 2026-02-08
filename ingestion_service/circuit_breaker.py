
import time
import logging
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.state = "CLOSED"
        self.opened_at = None

    def _open(self):
        self.state = "OPEN"
        self.opened_at = time.time()
        metrics.incr("circuit.open")
        logger.error("Circuit breaker opened")

    def _close(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.opened_at = None
        metrics.incr("circuit.closed")
        logger.info("Circuit breaker closed")

    def _half_open(self):
        self.state = "HALF_OPEN"
        metrics.incr("circuit.half_open")
        logger.warning("Circuit breaker half-open")

    def allow(self):
        if self.state == "OPEN":
            if time.time() - self.opened_at >= self.recovery_timeout:
                self._half_open()
                return True
            raise CircuitBreakerOpen("Circuit breaker is open")

        return True

    def success(self):
        if self.state in ("HALF_OPEN", "OPEN"):
            self._close()

    def failure(self):
        self.failure_count += 1
        metrics.incr("circuit.failure")

        if self.failure_count >= self.failure_threshold:
            self._open()
