#worker to process jobs 

import logging

from ingestion_service.pipeline import ingest_document

logger = logging.getLogger(__name__)


def run_ingestion_job(
    *,
    job_id: str,
    job_store,
    file_path,
    doc_id,
    embedder,
    vector_store,
):
    job_store.update(job_id, "running")

    try:
        ingest_document(
            file_path=file_path,
            doc_id=doc_id,
            embedder=embedder,
            vector_store=vector_store,
        )
        job_store.update(job_id, "completed")

    except Exception as exc:
        logger.exception("Ingestion job failed")
        job_store.update(job_id, "failed", str(exc))
