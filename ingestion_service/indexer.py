#Vector db client

from typing import List, Dict

class VectorStoreError(Exception):
    pass

class BaseVectorStore:
    """
    Abstract vector store interface.
    """
    
    def upsert(self,vectors:List[Dict]):
        raise NotImplementedError

    def delete(self,filter:Dict):
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self.vectors :Dict[str,Dict] = {}
    
    def upsert(self,vectors:List[Dict]):
        for vector in vectors:
            if "id" not in vector:
                raise VectorStoreError("Vector must have an id")
            self.vectors[vector['id']] = vector

    def delete(self,filter:Dict):
        """
        Delete all vectors whose metadata matches the filter.
        """

        keys_to_delete = []

        for key,value in self.vectors.items():
            metadata = value.get("metadata",{})
            if all(metadata.get(k) == v for k,v in filter.items()):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.vectors[key]


def index_chunks(chunks:List[Dict],vector_store:BaseVectorStore):
    """
    Persist chunks with embedding into the vector store.

    Each chunk MUST contain:
    -chunk_id
    -embedding
    -doc_id
    -sha256
    -chunk_index
    -chunk_start
    -chunk_end
    """
    vectors = []

    for chunk in chunks:
        if "chunk_id" not in chunk:
            raise VectorStoreError("Chunk must have a chunk_id")
        if "embedding" not in chunk:
            raise VectorStoreError("Chunk must have an embedding")
        
        vectors.append({
            "id":chunk['chunk_id'],
            "vector":chunk['embedding'],
            "metadata":{
                "doc_id":chunk['doc_id'],
                "sha256":chunk['sha256'],
                "chunk_index":chunk['chunk_index'],
                "chunk_start":chunk['chunk_start'],
                "chunk_end":chunk['chunk_end']
            }
        })
    
    vector_store.upsert(vectors)


def delete_document_version(doc_id : str,sha256 : str,vector_store : BaseVectorStore,):
    """
    Delete all chunks of a document version from the vector store.
    """
    vector_store.delete({"doc_id":doc_id,"sha256":sha256})









            
            