from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retriever with query-level caching.
    Caches:
    1. Query → embedding
    2. Query + params → results
    """

    def __init__(self, embedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store

        # Cache embeddings: normalized_query -> embedding
        self._embedding_cache: Dict[str, List[float]] = {}

        # Cache results: (query, top_k, filter) -> results
        self._result_cache: Dict[Tuple, List[Dict]] = {}

    def _normalize_query(self, query: str) -> str:
        return query.strip().lower()

    def _cache_key(self, query: str, top_k: int, filter: Dict | None) -> Tuple:
        """
        Build a stable cache key.
        """
        filter_key = tuple(sorted(filter.items())) if filter else None
        return (query, top_k, filter_key)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: Dict | None = None,
    ) -> List[Dict]:

        norm_query = self._normalize_query(query)
        key = self._cache_key(norm_query, top_k, filter)

        # ✅ RESULT CACHE HIT (MOST IMPORTANT)
        if key in self._result_cache:
            logger.info(
                "Retriever result cache hit",
                extra={"query": norm_query},
            )
            return self._result_cache[key]

        # ---- EMBEDDING ----
        if norm_query in self._embedding_cache:
            logger.info(
                "Embedding cache hit",
                extra={"query": norm_query},
            )
            query_embedding = self._embedding_cache[norm_query]
        else:
            logger.info(
                "Embedding cache miss",
                extra={"query": norm_query},
            )
            query_embedding = self.embedder.embed([norm_query])[0]
            self._embedding_cache[norm_query] = query_embedding

        # ---- VECTOR SEARCH (ONLY ONCE) ----
        results = self.vector_store.search(
            vector=query_embedding,
            top_k=top_k,
            filter=filter,
        )

        # ✅ CACHE FINAL RESULTS
        self._result_cache[key] = results

        return results
