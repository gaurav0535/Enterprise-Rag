from ingestion_service.metrics import metrics


def test_metrics_counter():
    metrics.incr("test.counter")
    assert metrics.counters["test.counter"] == 1
