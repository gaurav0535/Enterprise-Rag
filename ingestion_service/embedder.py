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


def embed_chunks(
    chunks: List[Dict],
    embedder: BaseEmbedder,
    batch_size: int = 8,
    max_retries: int = 3,
) -> List[Dict]:

    texts = [c["text"] for c in chunks]
    embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        for attempt in range(1, max_retries + 1):
            try:
                batch_emb = embedder.embed(batch)
                embeddings.extend(batch_emb)
                break
            except Exception: # Catch generic exception as CircuitBreaker might raise different ones
                if attempt == max_retries:
                    raise
                time.sleep(2 ** attempt)

    for c, e in zip(chunks, embeddings):
        c["embeddings"] = e

    return chunks
