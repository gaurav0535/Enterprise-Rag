import pytest
from ingestion_service.rate_limiter import RateLimiter, RateLimitExceeded


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    key = "client-1"

    limiter.allow(key)
    limiter.allow(key)

    with pytest.raises(RateLimitExceeded):
        limiter.allow(key)
