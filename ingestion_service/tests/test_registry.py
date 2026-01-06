from ingestion_service.registry import InMemoryDocumentRegistry

def test_register_and_exists():
    registry = InMemoryDocumentRegistry()
    assert not registry.exists(doc_id="test",sha256="test")
    registry.register(doc_id="test",sha256="test")
    assert registry.exists(doc_id="test",sha256="test")


def test_delete():
    registry = InMemoryDocumentRegistry()
    registry.register(doc_id="test",sha256="test")
    registry.delete(doc_id="test",sha256="test")
    assert not registry.exists(doc_id="test",sha256="test")

