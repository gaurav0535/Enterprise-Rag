def test_tenant_isolation(tmp_path):
    from ingestion_service.pipeline import ingest_document
    from ingestion_service.embedder import MockEmbedder
    from ingestion_service.indexer import InMemoryVectorStore
    from ingestion_service.registry import InMemoryDocumentRegistry
    from ingestion_service.retriever import Retriever

    file = tmp_path / "doc.txt"
    file.write_text("hello world " * 20)

    embedder = MockEmbedder()
    store = InMemoryVectorStore()
    registry = InMemoryDocumentRegistry()

    ingest_document(
        tenant_id="A",
        file_path=file,
        doc_id="doc",
        embedder=embedder,
        vector_store=store,
        registry=registry,
    )

    ingest_document(
        tenant_id="B",
        file_path=file,
        doc_id="doc",
        embedder=embedder,
        vector_store=store,
        registry=registry,
    )

    retriever = Retriever(embedder, store)

    res_a = retriever.retrieve(tenant_id="A", query="hello")
    res_b = retriever.retrieve(tenant_id="B", query="hello")

    assert res_a
    assert res_b
    assert res_a != res_b

