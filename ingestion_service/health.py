# ingestion_service/health.py

from ingestion_service.metrics import metrics

FAILURE_THRESHOLD = 5
LATENCY_P95_THRESHOLD_MS = 2000

def evaluate_health():
    snapshot = metrics.snapshot()

    failures = (
        snapshot["counters"].get("ingest.failed", 0)
        + snapshot["counters"].get("query.failed", 0)
    )

    ingest_latency = snapshot["timings"].get("ingest.latency_ms")
    query_latency = snapshot["timings"].get("query.latency_ms")

    degraded = False
    reasons = []

    if failures >= FAILURE_THRESHOLD:
        degraded = True
        reasons.append("too_many_failures")

    if ingest_latency and ingest_latency["p95"] > LATENCY_P95_THRESHOLD_MS:
        degraded = True
        reasons.append("high_ingest_latency")

    if query_latency and query_latency["p95"] > LATENCY_P95_THRESHOLD_MS:
        degraded = True
        reasons.append("high_query_latency")

    return {
        "status": "degraded" if degraded else "ok",
        "reasons": reasons,
        "metrics": snapshot,
    }
