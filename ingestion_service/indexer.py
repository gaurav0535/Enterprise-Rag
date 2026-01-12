# ingestion_service/indexer.py

from typing import List, Dict
import logging
import math

logger = logging.getLogger(__name__)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)




class VectorStoreError(Exception):
    """Raised when vector store operations fail."""
    pass


class BaseVectorStore:
    """
    Abstract vector store interface.
    """

    def upsert(self, vectors: List[Dict]):
        raise NotImplementedError

    def delete(self, filter: Dict):
        raise NotImplementedError

    def search(self, vector: List[float], k: int = 5, filter: Dict | None = None):
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store for testing and local validation.
    """

    def __init__(self):
        self.vectors: Dict[str, Dict] = {}

    def upsert(self, vectors: List[Dict]):
        for vector in vectors:
            if "id" not in vector:
                raise VectorStoreError("Vector must have an 'id'")
            self.vectors[vector["id"]] = vector

        logger.info(
            "Upserted vectors",
            extra={"count": len(vectors)},
        )

    def delete(self, filter: Dict):
        """
        Delete all vectors whose metadata matches the filter.
        """
        keys_to_delete = []

        for key, value in self.vectors.items():
            metadata = value.get("metadata", {})
            if all(metadata.get(k) == v for k, v in filter.items()):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.vectors[key]

        logger.info(
            "Deleted vectors",
            extra={"count": len(keys_to_delete), "filter": filter},
        )
    
    def search(self, vector, top_k=5, filter=None):
        results = []

        for item in self.vectors.values():
            metadata = item.get("metadata", {})

            if filter:
                if not all(metadata.get(k) == v for k, v in filter.items()):
                    continue

            score = _cosine(vector, item["vector"])

            results.append({
                "id": item["id"],
                "score": score,
                "metadata": metadata,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

def index_chunks(
    chunks: List[Dict],
    vector_store: BaseVectorStore,
):
    """
    Persist chunks with embeddings into the vector store.

    Each chunk MUST contain:
    - chunk_id
    - embedding
    - doc_id
    - sha256
    - chunk_index
    - char_start
    - char_end
    """
    if not chunks:
        logger.warning("No chunks provided for indexing")
        return

    vectors = []

    required_fields = {
        "chunk_id",
        "embedding",
        "doc_id",
        "sha256",
        "chunk_index",
        "char_start",
        "char_end",
    }

    for i, chunk in enumerate(chunks):
        missing = required_fields - chunk.keys()
        if missing:
            raise VectorStoreError(
                f"Chunk at index {i} missing fields: {missing}"
            )

        vectors.append({
            "id": chunk["chunk_id"],
            "vector": chunk["embedding"],
            "metadata": {
                "doc_id": chunk["doc_id"],
                "sha256": chunk["sha256"],
                "chunk_index": chunk["chunk_index"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
            },
        })

    vector_store.upsert(vectors)


def delete_document_version(
    doc_id: str,
    sha256: str,
    vector_store: BaseVectorStore,
):
    """
    Delete all chunks of a specific document version from the vector store.
    """
    vector_store.delete({
        "doc_id": doc_id,
        "sha256": sha256,
    })
