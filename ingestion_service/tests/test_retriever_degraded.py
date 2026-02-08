from unittest.mock import MagicMock
from ingestion_service.retriever import Retriever
from ingestion_service.circuit_breaker import CircuitBreakerOpen


def test_retriever_degraded_mode():
    embedder = MagicMock()
    embedder.embed.side_effect = CircuitBreakerOpen()

    store = MagicMock()

    retriever = Retriever(embedder, store)
    results = retriever.retrieve("hello")

    assert results == []

