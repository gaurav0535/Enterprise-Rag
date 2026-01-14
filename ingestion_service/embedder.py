# ingestion_service/embedder.py

from typing import List, Dict
import time
import random
import logging
from ingestion_service.errors import EmbeddingError

logger = logging.getLogger(__name__)




class BaseEmbedder:
    """
    Abstract embedding interface.
    """

    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class MockEmbedder(BaseEmbedder):
    """
    Deterministic mock embedder for tests.
    """

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[float(len(t))] for t in texts]


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
        logger.warning("No chunks received for embedding")
        return []

    texts = []
    for i, chunk in enumerate(chunks):
        if "text" not in chunk:
            raise EmbeddingError(f"Chunk at index {i} missing 'text'")
        texts.append(chunk["text"])
    logger.info(
        "Embedding batch",
        extra={
            "component": "embedder",
            "action": "embed",
        },
    )
    embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        for attempt in range(1, max_retries + 1):
            try:
                logger.warning(
                "Embedding retry",
                extra={
                    "component": "embedder",
                    "action": "retry",
                },
            )
                batch_embeddings = embedder.embed(batch)

                if len(batch_embeddings) != len(batch):
                    raise EmbeddingError(
                        "Embedding count does not match batch size"
                    )

                embeddings.extend(batch_embeddings)
                break

            except EmbeddingError as exc:
                logger.warning(
                    "Embedding batch failed",
                    extra={
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
        chunk["embedding"] = emb

    return chunks
