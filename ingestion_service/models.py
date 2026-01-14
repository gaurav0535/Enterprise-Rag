#pydentic  schemas 

from pydantic import BaseModel
from typing import Optional , Dict , List 

class IngestResponse(BaseModel):
    job_id: str
    status: str
    file_name:str

class HealthResponse(BaseModel):
    status: str


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filter: Dict | None = None

class QueryResult(BaseModel):
    id : set
    score : float
    metadata : Dict

class QueryResponse(BaseModel):
    results : List[QueryResult]

