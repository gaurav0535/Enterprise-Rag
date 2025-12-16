#pydentic  schemas 

from pydantic import BaseModel
from typing import Optional

class IngestResponse(BaseModel):
    job_id: str
    status: str
    file_name:str

class HealthResponse(BaseModel):
    status: str

