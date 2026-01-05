# ingestion_service/app.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from uuid import uuid4
from pathlib import Path
import shutil
import logging

from ingestion_service.models import IngestResponse, HealthResponse
from ingestion_service.config import STORAGE_DIR


logger = logging.getLogger(__name__)

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
        "status": "queued",
        "filename": file.filename,
    }
