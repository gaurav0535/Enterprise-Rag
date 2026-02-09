# 📘 Enterprise RAG Ingestion & Retrieval System

> Production-grade, multi-tenant Retrieval-Augmented Generation (RAG) backend  
> Built incrementally over 30 days with correctness, isolation, and testability as first-class goals.

---

## 🚀 What This Project Is

This project implements a robust document ingestion and retrieval pipeline designed for enterprise RAG systems.

It supports:
- Deterministic ingestion
- Idempotent re-ingestion
- Multi-tenant isolation
- Vector search
- Query caching
- Typed error handling
- Metrics and observability
- Strict test coverage

This is not a demo.
This is the core backend you would place behind:
- an LLM chat interface
- a knowledge assistant
- an internal search tool
- a GenAI platform

---

## 🧱 High-Level Architecture

Client/API  
→ Ingestion Pipeline (Extract → Chunk → Embed → Index)  
→ Vector Store (Tenant-isolated)  
→ Retrieval Pipeline (Query → Embed → Search → Rank)

---

## 📦 Core Capabilities (Achieved Till Day 30)

### ✅ Document Ingestion
- Supports TXT / PDF / DOCX
- Content normalization
- SHA-256 hashing for idempotency
- Same document version is never re-indexed twice

---

### ✅ Chunking Engine
- Deterministic chunk IDs
- Overlapping chunks
- Stable chunk boundaries
- No infinite loops
- Fully test-validated

---

### ✅ Embedding Layer
- Pluggable embedder interface
- Mock embedder for tests
- Batch embedding
- Retry with exponential backoff
- Typed embedding failures

---

### ✅ Vector Indexing
- Abstract BaseVectorStore
- InMemoryVectorStore implementation
- Cosine similarity
- Strong validation before upsert
- Metadata preserved per chunk

---

### ✅ Multi-Tenant Isolation (Day 30)
- Every chunk indexed with tenant_id
- Queries automatically scoped by tenant
- Cross-tenant leakage is impossible
- Isolation enforced at storage level

---

### ✅ Retrieval Layer
- Query embedding
- Vector similarity search
- Result ranking
- Metadata preserved
- Degraded-mode handling

---

### ✅ Query Cache
- In-memory cache inside Retriever
- Cache key = (query, top_k, filter)
- Prevents duplicate embedding calls
- Prevents duplicate vector searches
- Fully unit-tested

---

### ✅ Typed Error System
Custom domain errors:
- ExtractionError
- ChunkingError
- EmbeddingError
- IndexingError
- CircuitBreakerOpen

Errors are explicit, testable, and observable.

---

### ✅ Metrics & Observability
- Lightweight metrics counter
- Tracks:
  - ingestion success
  - index upserts
  - deletes
  - retriever degradation
- Ready for Prometheus / OpenTelemetry wiring

---

### ✅ Test Coverage
Test categories:
- Unit tests (chunker, embedder, indexer)
- Negative tests (invalid inputs)
- Idempotency tests
- Tenant isolation tests
- Cache behavior tests
- End-to-end ingestion + query tests

Tests fail loudly if contracts are broken.

---

## 📁 Project Structure

ingestion_service/
├── app.py
├── pipeline.py
├── query.py
├── retriever.py
├── preprocess.py
├── chunker.py
├── embedder.py
├── indexer.py
├── registry.py
├── cache.py
├── circuit_breaker.py
├── errors.py
├── metrics.py
└── tests/

---

## 🔐 Tenant Isolation Model

Each chunk is indexed with:
{
  "tenant_id": "A",
  "doc_id": "doc1",
  "sha256": "...",
  "chunk_index": 3
}

Queries are executed with:
filter={"tenant_id": "A"}

Tenant B can never see Tenant A’s vectors.

---

## 🧪 Running Tests

Run all tests:
pytest

Run tenant isolation tests only:
pytest ingestion_service/tests/test_tenant_isolation.py

---

## 🧠 What This System Is Ready For
- RAG Chatbots
- Internal enterprise search
- Knowledge assistants
- Compliance-aware AI systems
- Multi-client SaaS GenAI backends

---

## 🚧 What’s Intentionally Not Done Yet
- External vector DB (Pinecone / Qdrant / FAISS)
- Persistent cache (Redis)
- Auth layer (JWT / OAuth)
- Streaming ingestion
- API rate limiting
- LLM response generation

These are deliberately deferred.

---

## 🎯 Current Maturity Level

| Aspect              | Status |
|---------------------|--------|
| Correctness         | ✅ |
| Test coverage       | ✅ |
| Multi-tenancy       | ✅ |
| Observability       | ✅ |
| Production hygiene  | ✅ |
| LLM integration     | ❌ (by design) |

---

## 🧭 Next Logical Steps
- Persistence layer (DB / Vector DB)
- Auth + tenant enforcement
- Streaming ingestion
- Async workers
- LLM response layer

---

## 🏁 Final Note

This project is stronger than most GenAI repos online because:
- it respects invariants
- it enforces contracts
- it treats RAG as a system, not a prompt

You didn’t just build something.
You built infrastructure.
