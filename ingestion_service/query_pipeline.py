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

    return retriever.retrieve(tenant_id=tenant_id, query=query,top_k=top_k,filter=filter)
    