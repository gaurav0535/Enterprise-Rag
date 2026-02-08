from ingestion_service.pipeline import ingest_document
from ingestion_service.embedder import MockEmbedder
from ingestion_service.indexer import InMemoryVectorStore
from unittest.mock import MagicMock


def test_reingest_same_document(tmp_path):
    """
    Ingesting same document twice should not corrupt state
    """
    file = tmp_path / "doc.txt"
    file.write_text("hello world " * 50)

    store = InMemoryVectorStore()

    ingest_document(
        tenant_id="T1",
        file_path=file,
        doc_id="doc1",
        embedder=MockEmbedder(),
        vector_store=store,
        registry=MagicMock(),
    )

    vector_count_after_first = len(store.vectors)

    ingest_document(
        tenant_id="T1",
        file_path=file,
        doc_id="doc1",
        embedder=MockEmbedder(),
        vector_store=store,
        registry=MagicMock(),
    )

    vector_count_after_second = len(store.vectors)

    assert vector_count_after_second == vector_count_after_first
