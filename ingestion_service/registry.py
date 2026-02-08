# ingestion_service/registry.py

class BaseDocumentRegistry:
    def exists(self, tenant_id: str, doc_id: str, sha256: str) -> bool:
        raise NotImplementedError

    def register(self, tenant_id: str, doc_id: str, sha256: str):
        raise NotImplementedError


class InMemoryDocumentRegistry(BaseDocumentRegistry):
    def __init__(self):
        self._data = set()

    def exists(self, tenant_id: str, doc_id: str, sha256: str) -> bool:
        return (tenant_id, doc_id, sha256) in self._data

    def register(self, tenant_id: str, doc_id: str, sha256: str):
        self._data.add((tenant_id, doc_id, sha256))

    def delete(self, tenant_id: str, doc_id: str, sha256: str):
        self._data.discard((tenant_id, doc_id, sha256))

    def get(self, tenant_id: str, doc_id: str) -> Dict | None:
        for t, d, s in self._data:
            if t == tenant_id and d == doc_id:
                return {"doc_id": d, "sha256": s, "tenant_id": t}
        return None
