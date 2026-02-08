import logging
from typing import List, Dict

from ingestion_service.circuit_breaker import CircuitBreakerOpen
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, embedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 5, filter: Dict | None = None):
        try:
            query_vector = self.embedder.embed([query])[0]
            return self.vector_store.search(
                vector=query_vector,
                k=top_k,
                filter=filter,
            )

        except CircuitBreakerOpen:
            logger.warning("Retriever running in degraded mode")
            metrics.incr("retriever.degraded")
            return []

        except Exception:
            logger.exception("Retriever failure")
            raise
