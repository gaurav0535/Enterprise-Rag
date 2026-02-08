# ingestion_service/pipeline.py

from ingestion_service.preprocess import extract_text
from ingestion_service.chunker import chunk_text
from ingestion_service.embedder import embed_chunks
from ingestion_service.indexer import index_chunks


def ingest_document(file_path, doc_id, embedder, vector_store):
    extracted = extract_text(file_path)
    text = extracted["text"]
    sha256 = extracted["metadata"]["sha256"]

    chunks = chunk_text(text, doc_id, sha256)
    chunks = embed_chunks(chunks, embedder)

    index_chunks(chunks, vector_store)

    return len(chunks)
