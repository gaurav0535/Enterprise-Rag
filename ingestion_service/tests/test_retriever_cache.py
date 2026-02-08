from unittest.mock import MagicMock
from ingestion_service.retriever import Retriever


def test_retriever_uses_cache():
    embedder = MagicMock()
    vector_store = MagicMock()

    embedder.embed.return_value = [[1.0]]
    vector_store.search.return_value = [{"id": "c1"}]

    retriever = Retriever(embedder, vector_store)

    r1 = retriever.retrieve(tenant_id="T1", query="hello")
    r2 = retriever.retrieve(tenant_id="T1", query="hello")

    assert r1 == r2
    embedder.embed.assert_called_once()
    vector_store.search.assert_called_once()
