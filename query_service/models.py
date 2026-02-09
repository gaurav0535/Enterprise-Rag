# query_service/models.py
from pydantic import BaseModel
from typing import List, Dict, Optional


class QueryRequest(BaseModel):
    query: str
    tenant_id: str
    top_k: int = 5
    filter: Optional[Dict] = None


class QueryResult(BaseModel):
    chunk_id: str
    score: float
    metadata: Dict


class QueryResponse(BaseModel):
    results: List[QueryResult]
