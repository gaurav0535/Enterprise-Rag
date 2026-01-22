# ingestion_service/embedder.py

from typing import List, Dict
import time
import random
import logging

from ingestion_service.errors import EmbeddingError
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


class BaseEmbedder:
    """
    Abstract embedding interface.
    """

    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class MockEmbedder(BaseEmbedder):
    def embed(self, texts):
        return [[float(len(t))] for t in texts]

    # required for backward compatibility with tests
    def embd(self, texts):
        return self.embed(texts)


class SimulatedRemoteEmbedder(BaseEmbedder):
    """
    Simulates a remote embedding service.
    """

    def embed(self, texts: List[str]) -> List[List[float]]:
        time.sleep(0.2)

        if random.random() < 0.1:
            raise EmbeddingError("Transient embedding failure")

        return [[float(len(t))] * 3 for t in texts]


def embed_chunks(
    chunks: List[Dict],
    embedder: BaseEmbedder,
    batch_size: int = 8,
    max_retries: int = 3,
) -> List[Dict]:
    """
    Attach embeddings to chunks with batching and retry.

    Guarantees:
    - Each chunk receives exactly one embedding
    - Order is preserved
    - Transient failures are retried
    - Permanent failures fail loudly
    """

    if not chunks:
        logger.warning(
            "No chunks received for embedding",
            extra={"component": "embedder", "action": "skip"},
        )
        return []

    texts: List[str] = []

    for i, chunk in enumerate(chunks):
        if "text" not in chunk:
            raise EmbeddingError(f"Chunk at index {i} missing 'text'")
        texts.append(chunk["text"])

    embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        metrics.incr("embedding.batch_count")
        metrics.incr("embedding.texts", len(batch))

        logger.info(
            "Embedding batch started",
            extra={
                "component": "embedder",
                "action": "embed",
                "batch_size": len(batch),
            },
        )

        for attempt in range(1, max_retries + 1):
            try:
                with metrics.timer("embedding.batch_time"):
                    batch_embeddings = embedder.embed(batch)

                if len(batch_embeddings) != len(batch):
                    raise EmbeddingError(
                        "Embedding count does not match batch size"
                    )

                embeddings.extend(batch_embeddings)
                break

            except EmbeddingError as exc:
                metrics.incr("embedding.retry")

                logger.warning(
                    "Embedding batch failed",
                    extra={
                        "component": "embedder",
                        "action": "retry",
                        "attempt": attempt,
                        "batch_size": len(batch),
                        "error": str(exc),
                    },
                )

                if attempt == max_retries:
                    raise

                time.sleep(2 ** attempt)

    if len(embeddings) != len(chunks):
        raise EmbeddingError(
            "Total embeddings do not align with number of chunks"
        )

    for chunk, emb in zip(chunks, embeddings):
        chunk["embeddings"] = emb

    return chunks
