import pytest
from unittest.mock import MagicMock
from ingestion_service.indexer import (
    InMemoryVectorStore,
    index_chunks,
    delete_document_version,
    BaseVectorStore
)

from ingestion_service.indexer import InMemoryVectorStore
from ingestion_service.errors import IndexingError


class TestInMemoryVectorStore:
    def test_upsert_success(self):
        store = InMemoryVectorStore()
        vectors = [
            {"id": "1", "vector": [0.1, 0.2], "metadata": {"key": "val"}},
            {"id": "2", "vector": [0.3, 0.4]}
        ]
        store.upsert(vectors)
        assert len(store.vectors) == 2
        assert store.vectors["1"] == vectors[0]
        assert store.vectors["2"] == vectors[1]

    def test_upsert_missing_id(self):
        store = InMemoryVectorStore()
        vectors = [{"vector": [0.1, 0.2]}]
        with pytest.raises(IndexingError, match="Vector must have an id"):
            store.upsert(vectors)

    def test_delete_success(self):
        store = InMemoryVectorStore()
        store.vectors = {
            "1": {"id": "1", "metadata": {"doc_id": "A", "k": "v"}},
            "2": {"id": "2", "metadata": {"doc_id": "A", "k": "v2"}},
            "3": {"id": "3", "metadata": {"doc_id": "B"}}
        }
        
        # Delete where doc_id is A
        store.delete({"doc_id": "A"})
        
        assert "1" not in store.vectors
        assert "2" not in store.vectors
        assert "3" in store.vectors

    def test_delete_multiple_filters(self):
        store = InMemoryVectorStore()
        store.vectors = {
            "1": {"id": "1", "metadata": {"doc_id": "A", "version": "1"}},
            "2": {"id": "2", "metadata": {"doc_id": "A", "version": "2"}},
        }
        
        store.delete({"doc_id": "A", "version": "1"})
        assert "1" not in store.vectors
        assert "2" in store.vectors

    def test_delete_no_match(self):
        store = InMemoryVectorStore()
        store.vectors = {
            "1": {"id": "1", "metadata": {"doc_id": "A"}}
        }
        store.delete({"doc_id": "B"})
        assert "1" in store.vectors


class TestIndexChunks:
    def test_index_chunks_success(self):
        mock_store = MagicMock(spec=BaseVectorStore)
        chunks = [
            {
                "chunk_id": "c1",
                "embeddings": [0.1, 0.1],
                "doc_id": "d1",
                "sha256": "hash",
                "chunk_index": 0,
                "char_start": 0,
                "char_end": 10,
                "tenant_id": "T1"
            }
        ]
        
        index_chunks(chunks=chunks, vector_store=mock_store)
        
        mock_store.upsert.assert_called_once()
        call_args = mock_store.upsert.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["id"] == "c1"
        assert call_args[0]["vector"] == [0.1, 0.1]
        assert call_args[0]["metadata"]["doc_id"] == "d1"

    def test_index_chunks_missing_id(self):
        mock_store = MagicMock(spec=BaseVectorStore)
        chunks = [{"embedding": [0.1]}]
        with pytest.raises(IndexingError, match="missing.*chunk_id"):
            index_chunks(chunks=chunks, vector_store=mock_store)

    def test_index_chunks_missing_embedding(self):
        mock_store = MagicMock(spec=BaseVectorStore)
        chunks = [{"chunk_id": "c1"}]
        with pytest.raises(IndexingError, match="missing.*embeddings"):
            index_chunks(chunks=chunks, vector_store=mock_store)


def test_delete_document_version():
    mock_store = MagicMock(spec=BaseVectorStore)
    doc_id = "doc1"
    sha256 = "hash123"
    
    delete_document_version(doc_id=doc_id, sha256=sha256, vector_store=mock_store)
    
    mock_store.delete.assert_called_once_with({"doc_id": doc_id, "sha256": sha256})
