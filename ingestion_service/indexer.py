from typing import List, Dict
import logging
import math

from ingestion_service.errors import IndexingError
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class BaseVectorStore:
    def upsert(self, vectors: List[Dict]):
        raise NotImplementedError

    def delete(self, filter: Dict):
        raise NotImplementedError

    def search(self, vector, top_k=5, filter=None):
        raise NotImplementedError


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

    def search(self, vector, top_k=5, filter=None):
        results = []

        for item in self.vectors.values():
            meta = item.get("metadata", {})
            if filter:
                if not all(meta.get(k) == v for k, v in filter.items()):
                    continue

            score = _cosine(vector, item["vector"])
            results.append({
                "id": item["id"],
                "score": score,
                "metadata": meta,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def index_chunks(
    *,
    chunks: List[Dict],
    vector_store: BaseVectorStore,
):
    if not chunks:
        return

    required = {
        "chunk_id",
        "embeddings",
        "doc_id",
        "sha256",
        "chunk_index",
        "char_start",
        "char_end",
        "tenant_id",
    }

    vectors = []

    for i, c in enumerate(chunks):
        missing = required - c.keys()
        if missing:
            raise IndexingError(f"Chunk {i} missing {missing}")

        vectors.append({
            "id": c["chunk_id"],
            "vector": c["embeddings"],
            "metadata": {
                "doc_id": c["doc_id"],
                "sha256": c["sha256"],
                "chunk_index": c["chunk_index"],
                "char_start": c["char_start"],
                "char_end": c["char_end"],
                "tenant_id": c["tenant_id"],
            },
        })

    vector_store.upsert(vectors)

def delete_document_version(
    *,
    doc_id: str,
    sha256: str,
    vector_store: BaseVectorStore,
):
    """
    Delete all vectors belonging to a specific document version.
    """
    vector_store.delete(
        {
            "doc_id": doc_id,
            "sha256": sha256,
        }
    )
    metrics.incr("indexer.delete_count")