from ingestion_service.jobs import JobStore

def test_job_lifecycle():
    store = JobStore()
    job_id = store.create()
    assert store.get(job_id)["status"] == "queued"

    store.update(job_id, "running")
    assert store.get(job_id)["status"] == "running"

    store.update(job_id, "completed")
    assert store.get(job_id)["status"] == "completed"

