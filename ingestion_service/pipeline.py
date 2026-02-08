import logging

from ingestion_service.preprocess import extract_text
from ingestion_service.chunker import chunk_text
from ingestion_service.embedder import embed_chunks
from ingestion_service.indexer import index_chunks
from ingestion_service.circuit_breaker import CircuitBreakerOpen
from ingestion_service.metrics import metrics

logger = logging.getLogger(__name__)


def ingest_document(
    file_path,
    doc_id,
    embedder,
    vector_store,
    tenant_id: str | None = None,
):
    extracted = extract_text(file_path)
    text = extracted["text"]
    sha256 = extracted["sha256"]

    chunks = chunk_text(
        text=text,
        doc_id=doc_id,
        sha256=sha256,
    )

    if not chunks:
        logger.warning("No chunks generated")
        return 0

    try:
        chunks = embed_chunks(chunks, embedder)
        index_chunks(chunks, vector_store)

    except CircuitBreakerOpen:
        logger.error("Ingestion blocked by circuit breaker")
        metrics.incr("ingest.degraded")
        return 0

    return len(chunks)
