import logging
from typing import Dict, List, Optional, Tuple

from ingestion_service.circuit_breaker import CircuitBreakerOpen
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, embedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store
        self._cache = {}

    def retrieve(self, query: str, top_k: int, filter: Dict):
        if not query.strip():
            return []

        key = (query, top_k, frozenset(filter.items()))

        if key in self._cache:
            return self._cache[key]

        vector = self.embedder.embed([query])[0]
        results = self.vector_store.search(
            vector=vector,
            top_k=top_k,
            filter=filter,
        )

        self._cache[key] = results
        return results
