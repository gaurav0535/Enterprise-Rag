import pytest
from ingestion_service.indexer import BaseVectorStore
from ingestion_service.errors import IndexingError
from ingestion_service.pipeline import ingest_document
from ingestion_service.embedder import MockEmbedder


class FailingVectorStore(BaseVectorStore):
    def upsert(self, vectors):
        raise IndexingError("Index down")

    def delete(self, filter):
        pass


def test_indexing_failure_propagates(tmp_path):
    """
    Embedding succeeds, indexing fails → pipeline must stop
    """
    file = tmp_path / "doc.txt"
    file.write_text("hello world " * 50)

    with pytest.raises(IndexingError):
        ingest_document(
            file_path=file,
            doc_id="doc1",
            embedder=MockEmbedder(),
            vector_store=FailingVectorStore(),
        )
