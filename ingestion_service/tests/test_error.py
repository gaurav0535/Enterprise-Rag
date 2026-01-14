import pytest
from ingestion_service.chunker import chunk_text
from ingestion_service.errors import ChunkingError


def test_chunking_error():
    with pytest.raises(ChunkingError):
        chunk_text("text", "doc1", "hash", chunk_size=100, overlap=200)

