import pytest
from ingestion_service.circuit_breaker import CircuitBreaker, CircuitBreakerOpen


def test_circuit_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    cb.failure()
    cb.failure()

    with pytest.raises(CircuitBreakerOpen):
        cb.allow()
