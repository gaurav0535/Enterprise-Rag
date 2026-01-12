from pathlib import Path

from ingestion_service.pipeline import ingest_document
from ingestion_service.embedder import MockEmbedder
from ingestion_service.indexer import InMemoryVectorStore
from ingestion_service.retriever import Retriever
from ingestion_service.query_pipeline import query_documents


def test_query_returns_results(tmp_path):
    file = tmp_path / "doc.txt"
    file.write_text("hello world " * 50)

    embedder = MockEmbedder()
    store = InMemoryVectorStore()

    ingest_document(
        file_path=file,
        doc_id="doc1",
        embedder=embedder,
        vector_store=store,
    )

    retriever = Retriever(embedder, store)

    results = query_documents(
        query="hello",
        retriever=retriever,
        top_k=3,
    )

    assert len(results) > 0
