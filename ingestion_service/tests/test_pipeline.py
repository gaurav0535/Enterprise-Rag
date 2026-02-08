from pathlib import Path

from ingestion_service.pipeline import ingest_document
from ingestion_service.embedder import MockEmbedder
from ingestion_service.indexer import InMemoryVectorStore
from unittest.mock import MagicMock

def test_end_to_end_pipeline(tmp_path:Path):
    #Arraange 
    test_file = tmp_path/"text.txt"
    test_file.write_text("Hello world"*100)

    embedder = MockEmbedder()
    vector_store = InMemoryVectorStore()
    #Act
    chunk_count = ingest_document(
        tenant_id="test_tenant",
        file_path=test_file,
        doc_id="test_doc",
        embedder=embedder,
        vector_store=vector_store,
        registry=MagicMock(),
    )

    #Assert
    assert chunk_count > 0
    assert len(vector_store.vectors) == chunk_count