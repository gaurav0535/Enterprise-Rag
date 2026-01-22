import pytest
from ingestion_service.chunker import chunk_text
from ingestion_service.errors import ChunkingError


def test_chunker_rejects_invalid_overlap():
    """
    overlap >= chunk_size must fail immediately
    """
    with pytest.raises(ChunkingError):
        chunk_text(
            text="hello world",
            doc_id="doc1",
            sha256="hash",
            chunk_size=100,
            overlap=200,
        )
