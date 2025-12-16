#FastAPI app + /ingest route
from fastapi import FastAPI , UploadFile , File

from uuid import uuid4

from pathlib import Path
import shutil

from ingestion_service.models import IngestResponse , HealthResponse
from ingestion_service.config import STORAGE_DIR
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="Ingestion Service",description="API for ingesting files into the system")

@app.get("/health",response_model=HealthResponse)
def health():
    return {"status" : "ok"}


@app.post("/ingest",response_model=IngestResponse)
def ingest(file: UploadFile = File(...)):
    job_id = str(uuid4())

    target_path = STORAGE_DIR / f"{job_id}_{file.filename}"

    with target_path.open("wb") as f:
        shutil.copyfileobj(file.file,f)

    logging.info(f"Ingested file {file.filename} with job ID {job_id} and path is {target_path}" )
    

    return {"job_id": job_id, "status": "queued", "file_name": file.filename}
