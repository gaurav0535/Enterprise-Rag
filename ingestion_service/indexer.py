# ingestion_service/indexer.py

from typing import List, Dict
import math
import logging
from ingestion_service.errors import IndexingError
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class BaseVectorStore:
    def upsert(self, vectors: List[Dict]):
        raise NotImplementedError

    def delete(self, filter: Dict):
        raise NotImplementedError

    def search(self, vector: List[float], top_k: int = 5, filter: Dict | None = None):
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self.vectors: Dict[str, Dict] = {}

    def upsert(self, vectors: List[Dict]):
        for v in vectors:
            if "id" not in v:
                raise IndexingError("Vector must have an id")
            self.vectors[v["id"]] = v

    def delete(self, filter: Dict):
        self.vectors = {
            k: v for k, v in self.vectors.items()
            if not all(v["metadata"].get(fk) == fv for fk, fv in filter.items())
        }

    def search(self, vector, top_k=5, filter=None):
        results = []
        for v in self.vectors.values():
            if filter:
                if not all(v["metadata"].get(fk) == fv for fk, fv in filter.items()):
                    continue
            results.append({
                "id": v["id"],
                "score": _cosine(vector, v["vector"]),
                "metadata": v["metadata"],
            })
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]


def index_chunks(chunks: List[Dict], vector_store: BaseVectorStore):
    for chunk in chunks:
        if "chunk_id" not in chunk:
            raise IndexingError("Chunk must have a chunk_id")
        if "embeddings" not in chunk:
            raise IndexingError("Chunk must have an embedding")

    vectors = [{
        "id": c["chunk_id"],
        "vector": c["embeddings"],
        "metadata": {
            "doc_id": c["doc_id"],
            "sha256": c["sha256"],
            "chunk_index": c["chunk_index"],
            "char_start": c["char_start"],
            "char_end": c["char_end"],
        },
    } for c in chunks]

    vector_store.upsert(vectors)
    metrics.incr("indexer.upsert_count", len(vectors))


def delete_document_version(doc_id: str, sha256: str, vector_store: BaseVectorStore):
    vector_store.delete({"doc_id": doc_id, "sha256": sha256})
