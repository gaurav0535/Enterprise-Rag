from ingestion_service.cache import LRUCache


def test_lru_cache_basic():
    cache = LRUCache(capacity=2)

    cache.set("a", 1)
    cache.set("b", 2)

    assert cache.get("a") == 1
    cache.set("c", 3)

    assert cache.get("b") is None
    assert cache.get("c") == 3

