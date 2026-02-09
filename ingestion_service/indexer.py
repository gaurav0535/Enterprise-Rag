from typing import List, Dict
import math
import logging

from ingestion_service.errors import IndexingError
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class BaseVectorStore:
    def upsert(self, vectors: List[Dict]):
        raise NotImplementedError

    def delete(self, filter: Dict):
        raise NotImplementedError

    def search(self, vector: List[float], top_k: int, filter: Dict):
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self.vectors: Dict[str, Dict] = {}

    def upsert(self, vectors: List[Dict]):
        for v in vectors:
            if "id" not in v:
                raise IndexingError("Vector must have an id")
            self.vectors[v["id"]] = v

        metrics.incr("indexer.upsert", len(vectors))

    def delete(self, filter: Dict):
        to_delete = []
        for k, v in self.vectors.items():
            if all(v["metadata"].get(fk) == fv for fk, fv in filter.items()):
                to_delete.append(k)

        for k in to_delete:
            del self.vectors[k]

        metrics.incr("indexer.delete", len(to_delete))

    def search(self, vector: List[float], top_k: int, filter: Dict):
        results = []

        for v in self.vectors.values():
            metadata = v["metadata"]

            if not all(metadata.get(k) == val for k, val in filter.items()):
                continue

            score = _cosine(vector, v["vector"])
            results.append({
                "id": v["id"],
                "score": score,
                "metadata": metadata,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def index_chunks(chunks: List[Dict], vector_store: BaseVectorStore):
    if not chunks:
        return

    required = {
        "chunk_id",
        "embedding",
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
            "vector": c["embedding"],
            "metadata": {
                "tenant_id": c["tenant_id"],
                "doc_id": c["doc_id"],
                "sha256": c["sha256"],
                "chunk_index": c["chunk_index"],
                "char_start": c["char_start"],
                "char_end": c["char_end"],
            },
        })

    vector_store.upsert(vectors)
