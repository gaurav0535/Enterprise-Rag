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



logger = logging.getLogger(__name__)


# TEMP: local, in-memory dependencies
embedder = MockEmbedder()
vector_store = InMemoryVectorStore()

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
def ingest(file: UploadFile = File(...)):
    """
    Accept a file and persist it for downstream processing.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    job_id = str(uuid4())
    target_path = STORAGE_DIR / f"{job_id}_{file.filename}"

    try:
        with target_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.exception("Failed to persist uploaded file")
        raise HTTPException(status_code=500, detail="Failed to store file") from exc

    try:
        #1 Compute hash (cheap)
        extracted = extract_text(target_path)
        sha256 = extracted["metadata"]["sha256"]

        #2 Safe delete (idempotent)
        delete_document_version(doc_id=file.filename,sha256=sha256,
        vector_store=vector_store,
        )

        #3 Ingest
        chunk_count = ingest_document(file_path=target_path,
        doc_id=file.filename,
        embedder=embedder,
        vector_store=vector_store,
        )
    
    except Exception as exc:
        logger.exception("Failed to ingest file")
        raise HTTPException(status_code=500, detail="Failed to ingest file") from exc    

    logger.info(
        "File ingested",
        extra={
            "job_id": job_id,
            "filename": file.filename,
            "path": str(target_path),
        },
    )

    return {
        "job_id": job_id,
        "status": "completed",
        "file_name": file.filename,
        "chunks_indexed": chunk_count,
    }
