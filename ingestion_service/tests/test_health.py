# ingestion_service/tests/test_health.py

from ingestion_service.health import evaluate_health
from ingestion_service.metrics import metrics

def test_health_ok():
    result = evaluate_health()
    assert result["status"] in {"ok", "degraded"}

def test_health_degraded_on_failures():
    for _ in range(6):
        metrics.incr("ingest.failed")

    result = evaluate_health()
    assert result["status"] == "degraded"
    assert "too_many_failures" in result["reasons"]
