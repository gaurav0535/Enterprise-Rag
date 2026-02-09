from typing import List,Dict
from ingestion_service.retriever import Retriever

def query_documents(
    tenant_id: str,
    query : str,
    retriever : Retriever,
    top_k : int = 5,
    filter : Dict | None = None,
) -> List[Dict]:
    """
    End to end retrieval pipeline.
    """
    # Merge tenant_id into filter
    if filter is None:
        filter = {}
    filter["tenant_id"] = tenant_id

    return retriever.retrieve(query=query, top_k=top_k, filter=filter)
    