import logging
from pathlib import Path

from ingestion_service.preprocess import extract_text
from ingestion_service.chunker import chunk_text
from ingestion_service.embedder import embed_chunks
from ingestion_service.indexer import index_chunks
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


def ingest_document(
    *,
    tenant_id: str,
    file_path: Path,
    doc_id: str,
    embedder,
    vector_store,
):
    if not tenant_id:
        raise ValueError("tenant_id is required")

    extracted = extract_text(file_path)
    text = extracted["text"]
    sha256 = extracted["sha256"]

    chunks = chunk_text(
        text=text,
        doc_id=doc_id,
        sha256=sha256,
    )

    if not chunks:
        return 0

    for c in chunks:
        c["tenant_id"] = tenant_id

    chunks = embed_chunks(chunks, embedder)
    index_chunks(chunks, vector_store)

    metrics.incr("pipeline.ingest.success")
    return len(chunks)
