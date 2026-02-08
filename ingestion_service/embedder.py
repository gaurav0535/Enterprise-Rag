from typing import List, Dict
import time
import random
import logging

from ingestion_service.errors import EmbeddingError
from ingestion_service.metrics import metrics
from ingestion_service.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

logger = logging.getLogger(__name__)


class BaseEmbedder:
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class MockEmbedder(BaseEmbedder):
    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[float(len(t))] for t in texts]


class SimulatedRemoteEmbedder(BaseEmbedder):
    def embed(self, texts: List[str]) -> List[List[float]]:
        time.sleep(0.2)
        if random.random() < 0.3:
            raise EmbeddingError("Remote embedding failure")
        return [[float(len(t))] * 3 for t in texts]


class CircuitBreakerEmbedder(BaseEmbedder):
    """
    Embedder wrapped with circuit breaker
    """

    def __init__(self, embedder: BaseEmbedder):
        self.embedder = embedder
        self.breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=20,
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        self.breaker.allow()

        try:
            vectors = self.embedder.embed(texts)
            self.breaker.success()
            return vectors

        except Exception as exc:
            self.breaker.failure()
            logger.exception("Embedding failed")
            raise
