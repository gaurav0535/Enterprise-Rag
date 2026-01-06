from typing import Dict , Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentRegistryError(Exception):
    pass


class InMemoryDocumentRegistry:
    """
    In memory document registry.

    Act as the source of truth for document versions.
    
    """
    
    def __init__(self):
        self._registry: Dict[Tuple[str,str],str] = {}    

    def exists(self,doc_id:str,sha256:str) ->bool:
        """
        Check if the document already present 
        """
        return (doc_id,sha256) in self._registry

    def register(self,doc_id: str,sha256 :str,status:str = "completed"):
        """
        Register a new document version
        """
        key = (doc_id,sha256)
        if key in self._registry:
            raise DocumentRegistryError("Document already registered")
        
        self._registry[key] = status

        logger.info(
            "Registered document version ",
            extra={
                "doc_id": doc_id,
                "sha256": sha256,
                "status": status,
            },
        )

    def delete(self,doc_id:str,sha256:str):
        """
        Delete a document version
        """
        key = (doc_id,sha256)
        if key not in self._registry:
            raise DocumentRegistryError("Document not registered")
        
        self._registry.pop(key)

        logger.info(
            "Deleted document version",
            extra={
                "doc_id": doc_id,
                "sha256": sha256,
            },
        )
