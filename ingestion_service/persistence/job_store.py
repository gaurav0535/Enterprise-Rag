import json
import threading
from pathlib import Path
from typing import Dict

class PersistentJobStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict:
        with self.path.open("r") as f:
            return json.load(f)

    def _write(self, data: Dict):
        with self.path.open("w") as f:
            json.dump(data, f, indent=2)

    def create(self) -> str:
        with self.lock:
            data = self._read()
            job_id = str(len(data) + 1)
            data[job_id] = {
                "status": "queued",
                "error": None,
            }
            self._write(data)
            return job_id

    def update(self, job_id: str, status: str, error: str | None = None):
        with self.lock:
            data = self._read()
            if job_id not in data:
                return
            data[job_id]["status"] = status
            data[job_id]["error"] = error
            self._write(data)

    def get(self, job_id: str):
        return self._read().get(job_id)

    def all(self) -> Dict:
        return self._read()
    