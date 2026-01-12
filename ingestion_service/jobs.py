from typing import Dict
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class JobStore:
    """
    In memory job store.
    """
    def __init__(self):
        self._jobs: Dict[str,Dict] = {}

    def create(self) ->int:
        job_id = str(uuid4())
        self._jobs[job_id] = {"status": "queued"}
        logger.info("Jib created ",extra={"job_id":job_id})
        return job_id

    def update(self, job_id: str, status: str, error: str | None = None):    
        if job_id not in self._jobs:
            raise ValueError("Job not found")
        self._jobs[job_id]["status"] = status 
        if error :
            self._jobs[job_id]["error"] = error 
        logger.info("Job updated ",extra={"job_id":job_id,"error":error}) 

    def get(self,job_id: str) -> Dict | None:
        return self._jobs.get(job_id)

