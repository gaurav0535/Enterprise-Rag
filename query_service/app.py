# query_service/app.py
from fastapi import FastAPI
from query_service.models import QueryRequest, QueryResponse, QueryResult
from query_service.dependencies import retriever

app = FastAPI(
    title="Query Service",
    description="Read-only semantic search API",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_documents(req: QueryRequest):
    results = retriever.retrieve(
        tenant_id=req.tenant_id,
        query=req.query,
        top_k=req.top_k,
        filter=req.filter,
    )

    return {
        "results": [
            QueryResult(
                chunk_id=r["id"],
                score=r["score"],
                metadata=r["metadata"],
            )
            for r in results
        ]
    }
