# ingestion_service/indexer.py

from typing import List, Dict
import logging
import math

from ingestion_service.errors import IndexingError
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


# -------------------------
# Errors
# -------------------------
class VectorStoreError(Exception):
    """Raised when vector store operations fail."""


# -------------------------
# Utils
# -------------------------
def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# -------------------------
# Base Store
# -------------------------
class BaseVectorStore:
    def upsert(self, vectors: List[Dict]):
        raise NotImplementedError

    def delete(self, filter: Dict):
        raise NotImplementedError

    def search(self, vector: List[float], k: int = 5, filter: Dict | None = None):
        raise NotImplementedError


# -------------------------
# In-Memory Store
# -------------------------
class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self.vectors: Dict[str, Dict] = {}

    def upsert(self, vectors: List[Dict]):
        for v in vectors:
            if "id" not in v:
                raise IndexingError("Vector must have an id")
            self.vectors[v["id"]] = v

        metrics.incr("indexer.upsert_count", len(vectors))

    def delete(self, filter: Dict):
        to_delete = []

        for k, v in self.vectors.items():
            meta = v.get("metadata", {})
            if all(meta.get(fk) == fv for fk, fv in filter.items()):
                to_delete.append(k)

        for k in to_delete:
            del self.vectors[k]

        metrics.incr("indexer.delete_count")

    def search(self, vector, k=5, filter=None):
        results = []

        for item in self.vectors.values():
            meta = item.get("metadata", {})
            if filter and not all(meta.get(fk) == fv for fk, fv in filter.items()):
                continue

            score = _cosine(vector, item["vector"])
            results.append(
                {
                    "id": item["id"],
                    "score": score,
                    "metadata": meta,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]


# -------------------------
# Indexing Logic
# -------------------------
def index_chunks(chunks: List[Dict], vector_store: BaseVectorStore):
    if not chunks:
        logger.warning("No chunks provided for indexing")
        return

    vectors = []

    for i, chunk in enumerate(chunks):
        # ⛔ REQUIRED ORDER — tests depend on this
        if "chunk_id" not in chunk:
            raise IndexingError("Chunk must have a chunk_id")

        if "embedding" not in chunk:
            raise IndexingError("Chunk must have an embedding")

        if "doc_id" not in chunk:
            raise IndexingError("Chunk must have a doc_id")

        if "sha256" not in chunk:
            raise IndexingError("Chunk must have a sha256")

        if "chunk_index" not in chunk:
            raise IndexingError("Chunk must have a chunk_index")

        # tests use chunk_start / chunk_end (NOT char_*)
        if "chunk_start" not in chunk:
            raise IndexingError("Chunk must have a chunk_start")

        if "chunk_end" not in chunk:
            raise IndexingError("Chunk must have a chunk_end")

        vectors.append(
            {
                "id": chunk["chunk_id"],
                "vector": chunk["embedding"],
                "metadata": {
                    "doc_id": chunk["doc_id"],
                    "sha256": chunk["sha256"],
                    "chunk_index": chunk["chunk_index"],
                    "chunk_start": chunk["chunk_start"],
                    "chunk_end": chunk["chunk_end"],
                },
            }
        )

    vector_store.upsert(vectors)


def delete_document_version(doc_id: str, sha256: str, vector_store: BaseVectorStore):
    vector_store.delete(
        {
            "doc_id": doc_id,
            "sha256": sha256,
        }
    )
