from typing import List, Dict   
from ingestion_service.embedder import BaseEmbedder
from ingestion_service.indexer import BaseVectorStore

class Retriever:
    """
    Read only retrieval abstraction
    """
    def __init__(self,embedder:BaseEmbedder,vector_store:BaseVectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
    
    def retrieve(self,query:str,top_k:int=5,filter:Dict | None = None) -> List[Dict]:

        query_embedding = self.embedder.embed([query])[0]

        return self.vector_store.search(
            vector = query_embedding,
            top_k = top_k,
            filter = filter,
        )


