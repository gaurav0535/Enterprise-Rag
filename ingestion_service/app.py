from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pathlib import Path
import shutil
import logging

from ingestion_service.jobs import JobStore
from ingestion_service.workers import run_ingestion_job
from ingestion_service.embedder import MockEmbedder
from ingestion_service.indexer import InMemoryVectorStore
from ingestion_service.models import HealthResponse


from ingestion_service.persistence.job_store import PersistentJobStore
from ingestion_service.persistence.vector_store import PersistentVectorStore

job_store = PersistentJobStore(Path("./data/jobs.json"))
vector_store = PersistentVectorStore(Path("./data/vectors.json"))

# -------------------------------------------------------------------
# App setup
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ingestion Service",
    description="Asynchronous document ingestion pipeline",
)

# -------------------------------------------------------------------
# Global dependencies (TEMP: in-memory)
# -------------------------------------------------------------------

job_store = JobStore()
embedder = MockEmbedder()
vector_store = InMemoryVectorStore()

STORAGE_DIR = Path("./storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# Health
# -------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}

# -------------------------------------------------------------------
# Ingest (ASYNC)
# -------------------------------------------------------------------

@app.post("/ingest")
def ingest(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Accepts a file and schedules ingestion in the background.
    Returns immediately with a job_id.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # 1️⃣ Create job
    job_id = job_store.create()

    # 2️⃣ Persist file
    target_path = STORAGE_DIR / f"{job_id}_{file.filename}"
    try:
        with target_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.exception("Failed to store uploaded file")
        job_store.update(job_id, "failed", "file_write_error")
        raise HTTPException(status_code=500, detail="File upload failed") from exc

    # 3️⃣ Schedule background ingestion
    background_tasks.add_task(
        run_ingestion_job,
        job_id=job_id,
        job_store=job_store,
        file_path=target_path,
        doc_id=file.filename,
        embedder=embedder,
        vector_store=vector_store,
    )

    logger.info(
        "Ingestion job queued",
        extra={
            "job_id": job_id,
            "uploaded_filename": file.filename,
        },
    )

    return {
        "job_id": job_id,
        "status": "queued",
    }

# -------------------------------------------------------------------
# Job status
# -------------------------------------------------------------------

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """
    Returns job status.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job



from ingestion_service.lifecycle import on_startup, on_shutdown

@app.on_event("startup")
def startup_event():
    on_startup(job_store)

@app.on_event("shutdown")
def shutdown_event():
    on_shutdown()
