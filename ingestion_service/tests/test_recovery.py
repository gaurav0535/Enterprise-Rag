from ingestion_service.persistence.job_store import PersistentJobStore
from ingestion_service.lifecycle import on_startup
from pathlib import Path

def test_recovery_marks_running_jobs_failed(tmp_path):
    store = PersistentJobStore(tmp_path / "jobs.json")

    job_id = store.create()
    store.update(job_id, "running")

    on_startup(store)

    job = store.get(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "recovered_after_restart"
