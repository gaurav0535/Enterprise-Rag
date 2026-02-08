from fastapi import APIRouter, HTTPException, Request
from ingestion_service.rate_limiter import RateLimiter, RateLimitExceeded
from ingestion_service.query_pipeline import query_documents

router = APIRouter()

rate_limiter = RateLimiter(
    max_requests=5,
    window_seconds=60,
)


@router.post("/query")
def query(request: Request, payload: dict):
    client_id = request.client.host

    try:
        rate_limiter.allow(client_id)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        )

    return query_documents(
        query=payload["query"],
        top_k=payload.get("top_k", 5),
    )
