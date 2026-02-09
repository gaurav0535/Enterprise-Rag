# ingestion_service/tests/test_retriever.py

import pytest
from unittest.mock import MagicMock

from ingestion_service.retriever import Retriever
from ingestion_service.errors import EmbeddingError


def test_retriever_returns_results():
    # Arrange
    embedder = MagicMock()
    vector_store = MagicMock()

    embedder.embed.return_value = [[1.0, 2.0, 3.0]]
    vector_store.search.return_value = [
        {"id": "c1", "score": 0.9, "metadata": {"doc_id": "d1"}},
        {"id": "c2", "score": 0.8, "metadata": {"doc_id": "d1"}},
    ]

    retriever = Retriever(embedder, vector_store)

    # Act
    results = retriever.retrieve(query="hello", top_k=2, filter={"tenant_id": "T1"})

    # Assert
    assert len(results) == 2
    assert results[0]["id"] == "c1"

    embedder.embed.assert_called_once_with(["hello"])
    vector_store.search.assert_called_once()


def test_retriever_empty_query():
    embedder = MagicMock()
    vector_store = MagicMock()

    retriever = Retriever(embedder, vector_store)

    results = retriever.retrieve(query="   ", filter={"tenant_id": "T1"})

    assert results == []
    embedder.embed.assert_not_called()
    vector_store.search.assert_not_called()


def test_retriever_embedding_failure():
    embedder = MagicMock()
    vector_store = MagicMock()

    embedder.embed.side_effect = EmbeddingError("embedding failed")

    retriever = Retriever(embedder, vector_store)

    with pytest.raises(EmbeddingError):
        retriever.retrieve(query="hello", filter={"tenant_id": "T1"})
