# ingestion_service/embedder.py

from typing import List, Dict
import time
import random
import logging
from ingestion_service.errors import EmbeddingError

logger = logging.getLogger(__name__)


class BaseEmbedder:
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    # TEST COMPATIBILITY
    def embd(self, texts: List[str]) -> List[List[float]]:
        return self.embed(texts)


class MockEmbedder(BaseEmbedder):
    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[float(len(t))] for t in texts]


class SimulatedRemoteEmbedder(BaseEmbedder):
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

    texts = [c["text"] for c in chunks]
    embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        for attempt in range(max_retries):
            try:
                batch_emb = embedder.embed(batch)
                embeddings.extend(batch_emb)
                break
            except EmbeddingError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embeddings"] = emb  # REQUIRED BY TESTS

    return chunks
