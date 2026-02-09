from typing import Dict, List

from ingestion_service.retriever import Retriever


def query_documents(
    *,
    tenant_id: str,
    query: str,
    retriever: Retriever,
    top_k: int = 5,
) -> List[Dict]:

    if not tenant_id:
        return []

    return retriever.retrieve(
        query=query,
        top_k=top_k,
        filter={"tenant_id": tenant_id},
    )
