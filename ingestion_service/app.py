# ingestion_service/app.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from uuid import uuid4
from pathlib import Path
import shutil
import logging

from ingestion_service.models import IngestResponse, HealthResponse
from ingestion_service.config import STORAGE_DIR
from ingestion_service.pipeline import ingest_document
from ingestion_service.embedder import MockEmbedder
from ingestion_service.indexer import InMemoryVectorStore, delete_document_version
from ingestion_service.preprocess import extract_text
from ingestion_service.jobs import JobStore
from ingestion_service.registry import InMemoryDocumentRegistry
from ingestion_service.retriever import Retriever
from ingestion_service.query_pipeline import query_documents
from ingestion_service.models import QueryRequest, QueryResponse

from ingestion_service.logging_utils import configure_logging

from ingestion_services.errors import (
    IngestionError,
    ExtractionError,
    EmbeddingError,
    ChunkingError,
    IndexingError,
    RetrievalError,
)
from ingestion_service.metrics import metrics

configure_logging()


from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


# TEMP: local, in-memory dependencies
embedder = MockEmbedder()
vector_store = InMemoryVectorStore()

job_store = JobStore()
registry = InMemoryDocumentRegistry()  

retriever = Retriever(embedder=embedder,vector_store=vector_store)



app = FastAPI(
    title="Ingestion Service",
    description="API for ingesting files into the system",
)


@app.get("/health", response_model=HealthResponse)
def health():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Accept a file and persist it for downstream processing.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    job_id = job_store.create()
    target_path = STORAGE_DIR / f"{job_id}_{file.filename}"

    log_ctx = {
        "job_id":job_id,
        "doc_id":file.filename,
        "component":"app",
        "action":"ingest_request",
    }

    logger.info("Received ingest request", extra=log_ctx)

    try:
        with target_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
            logger.info(
                "File persisted to storage",
                extra={**log_ctx, "action": "persist"},
            )
    except Exception as exc:
        logger.exception(
            "Failed to store uploaded file",
            extra=log_ctx,
        )
        raise HTTPException(status_code=500, detail="Failed to store file") from exc

    background_tasks.add_task(run_ingestion_job,job_id,target_path,file.filename)
    logger.info(
        "Ingestion job enqueued",
        extra={**log_ctx, "action": "enqueue"},
    )
    return {
        "job_id": job_id,
        "status": "queued",
        "file_name": file.filename,
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def run_ingestion_job(job_id:str,file_path:Path,doc_id:str):

    job_store.update(job_id,"running")
    log_ctx = {
    "job_id": job_id,
    "doc_id": doc_id,
    "component": "pipeline",
    "action": "start",
    }
    logger.info("Ingestion job started", extra=log_ctx)

    try:
        with metrics.timer("ingestion.total_time"):
            extracted = extract_text(file_path)
            sha256 = extracted["metadata"]["sha256"]

            if registry.exists(doc_id,sha256):
                job_store.update(job_id,"completed")
                logger.info(
                    "Document version already ingested",
                    extra={**log_ctx, "action": "skip"},
                )
                return
            logger.info(
        "Deleting previous document version",
        extra={**log_ctx, "action": "delete"},
    )
            delete_document_version(doc_id=doc_id,sha256=sha256,
            vector_store=vector_store,
            )

            ingest_document(
                file_path = file_path,
                doc_id = doc_id,
                embedder = embedder,
                vector_store = vector_store,
            )

            registry.register(doc_id,sha256)
        metrics.incr("ingestion.success")
        logger.info(
            "Ingestion job completed",
            extra={**log_ctx, "action": "end"},
        )
        job_store.update(job_id,"completed")

    except (ExtractionError, ChunkingError, EmbeddingError, IndexingError) as exc:
        logger.exception("Failed to run ingestion job",extra=log_ctx)
        job_store.update(job_id,"failed",str(exc))

        logger.exception(
            "Ingestion job failed",
            extra={**log_ctx, "action": "fail"},
        )
        raise HTTPException(status_code=500, detail="Failed to run ingestion job") from exc
    

@app.post("/query",response_model=QueryResponse)
def query(req : QueryRequest):

    log_ctx = {
        "component": "app",
        "action": "search",
    }
    logger.info(f"Received query: {req.query}", extra=log_ctx)

    try:
        results = query_documents(
            query=req.query,
            retriever=retriever,
            top_k=req.top_k,
            filter=req.filter,
        )

        logger.info(
            "Query completed",
            extra={**log_ctx, "count": len(results)},
        )

        return {"results": results}
    
    except Exception as exc:
        logger.exception("Query failed", extra=log_ctx)
        raise HTTPException(status_code=500, detail="Query failed") from exc

