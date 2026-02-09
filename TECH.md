# Enterprise RAG System – Technical Implementation Documentation

This document explains how the Enterprise RAG system is implemented internally.
It focuses on architecture, invariants, control flow, and design decisions.
This is written for engineers, reviewers, and future maintainers.

================================================================================
SYSTEM OVERVIEW
================================================================================

The system is a production-grade Retrieval-Augmented Generation (RAG) backend with:

- Deterministic ingestion
- Idempotent indexing
- Typed failures
- Tenant isolation
- Query caching
- Metrics and observability
- Strong test coverage

The architecture is intentionally explicit, layered, and replaceable.

================================================================================
INGESTION PIPELINE
================================================================================

File: ingestion_service/pipeline.py

Responsibilities:
- Orchestrates the full ingestion lifecycle
- Enforces idempotency
- Coordinates deletion and reindexing

Execution Flow:
1. Extract text and metadata
2. Compute SHA-256 hash
3. Check document registry
4. Chunk text deterministically
5. Embed chunks with retry
6. Index vectors
7. Register document version

Pipeline:
file
 → extract_text
 → chunk_text
 → embed_chunks
 → index_chunks
 → registry.register

Guarantees:
- Same document version is ingested once
- Partial failures never leave stale vectors
- Re-ingestion is safe and deterministic

================================================================================
TEXT EXTRACTION AND NORMALIZATION
================================================================================

File: ingestion_service/preprocess.py

Supported formats:
- .txt
- .docx
- .pdf (native extraction with OCR fallback)

Output contract:
{
  "text": "<normalized_text>",
  "metadata": {
      "sha256": "<file_hash>",
      "source": "<file_type>"
  }
}

Design notes:
- File type detection via extension
- Unsupported formats fail fast
- OCR logic is isolated
- Text normalization is explicit and testable

================================================================================
CHUNKING ENGINE
================================================================================

File: ingestion_service/chunker.py

Chunk identity:
chunk_id = SHA256(doc_id + file_sha256 + chunk_index)

Chunk fields:
- chunk_id
- doc_id
- sha256
- chunk_index
- char_start
- char_end
- text

Invariants:
- overlap < chunk_size
- No empty chunks
- No infinite loops
- Stable output for identical input

Why determinism matters:
- Enables safe re-ingestion
- Enables version deletion
- Prevents duplicate vectors
- Makes tests reliable

================================================================================
EMBEDDING LAYER
================================================================================

File: ingestion_service/embedder.py

Architecture:
chunks → embed_chunks → embedder.embed()

Features:
- Pluggable embedder interface
- Batch processing
- Exponential backoff retry
- Strict output validation

Failure model:
- Transient failures retry
- Permanent failures raise EmbeddingError
- Partial batch failures never leak downstream

================================================================================
VECTOR INDEXING
================================================================================

File: ingestion_service/indexer.py

BaseVectorStore interface:
- upsert(vectors)
- delete(filter)
- search(vector, top_k, filter)

InMemoryVectorStore:
- Used for correctness and tests
- Stores vectors by chunk_id
- Uses cosine similarity

Validation rules:
- chunk_id must exist
- embedding must exist
- required metadata must exist

Errors are explicit:
IndexingError("Chunk must have an embedding")

================================================================================
DOCUMENT VERSIONING AND IDEMPOTENCY
================================================================================

Files:
- ingestion_service/registry.py
- ingestion_service/pipeline.py

Registry tracks:
(doc_id, sha256)

Behavior:
- If version exists → skip ingestion
- If new version → delete old vectors and reindex

Result:
- No duplicate vectors
- Clean document upgrades
- Idempotent ingestion

================================================================================
TENANT ISOLATION
================================================================================

Files:
- pipeline.py
- indexer.py
- retriever.py

Mechanism:
- tenant_id injected into every chunk
- Stored in vector metadata
- Every search filtered by tenant_id

Filter example:
{"tenant_id": tenant_id}

Guarantees:
- Zero cross-tenant leakage
- Isolation enforced at storage level
- Safe for SaaS workloads

================================================================================
RETRIEVAL PIPELINE
================================================================================

File: ingestion_service/retriever.py

Flow:
1. Validate query
2. Check cache
3. Embed query
4. Vector search
5. Cache results
6. Return ranked matches

Failure handling:
- Circuit breaker triggers degraded mode
- Metrics incremented
- No exception leakage to API

================================================================================
QUERY CACHE
================================================================================

File: ingestion_service/retriever.py

Cache key:
(query, top_k, frozenset(filter.items()))

Cached items:
- Query embedding
- Vector search results

Guarantees:
- Same query embeds once
- Same query searches once
- Verified by strict mock-based tests

================================================================================
METRICS AND OBSERVABILITY
================================================================================

File: ingestion_service/metrics.py

Design:
- Minimal counter abstraction
- No external dependency
- Replaceable with Prometheus or OpenTelemetry

Examples:
metrics.incr("indexer.upsert_count")
metrics.incr("retriever.degraded")

Metrics are emitted at state transitions.

================================================================================
TYPED ERROR SYSTEM
================================================================================

File: ingestion_service/errors.py

Error types:
- ExtractionError
- ChunkingError
- EmbeddingError
- IndexingError
- CircuitBreakerOpen

Why typed errors:
- Predictable control flow
- Strong test assertions
- Meaningful logs

No generic Exception in core logic.

================================================================================
TESTING STRATEGY
================================================================================

Directory: ingestion_service/tests/

Coverage:
- Unit tests
- Contract tests
- End-to-end pipeline tests
- Tenant isolation tests
- Cache behavior tests

Principle:
If a test fails, a system guarantee was broken.

================================================================================
WHY THIS ARCHITECTURE SCALES
================================================================================

- Deterministic → predictable
- Typed → debuggable
- Layered → replaceable
- Isolated → secure
- Tested → trustworthy

This backend is built to survive production scale, not demos.

================================================================================
FUTURE EXTENSIONS ENABLED
================================================================================

- LLM orchestration layers
- Streaming ingestion
- Persistent vector databases
- Enterprise SaaS deployment
- Multi-region scaling

The foundation is complete.



# Enterprise RAG System – Technical Implementation Documentation

This document explains how the Enterprise RAG system is implemented internally.
It focuses on architecture, invariants, control flow, and design decisions.
This is written for engineers, reviewers, and future maintainers.

================================================================================
ARCHITECTURE DIAGRAM
================================================================================

                          ┌────────────────────────┐
                          │        Client          │
                          │  (Upload / Query API)  │
                          └───────────┬────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │        FastAPI App        │
                         │        (app.py)           │
                         └────────────┬─────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────┐           ┌─────────────────┐           ┌──────────────────┐
│ Ingestion API│           │  Query API      │           │   Health / Admin  │
│  /ingest     │           │  /query         │           │   Endpoints       │
└──────┬───────┘           └────────┬────────┘           └──────────────────┘
       │                              │
       ▼                              ▼
┌────────────────────┐      ┌────────────────────────┐
│ Ingestion Pipeline │      │      Retriever          │
│  pipeline.py       │      │  retriever.py           │
└──────┬─────────────┘      └──────────┬─────────────┘
       │                                │
       ▼                                ▼
┌────────────────────┐      ┌────────────────────────┐
│  Text Extraction   │      │   Query Cache (LRU)    │
│  preprocess.py     │      └──────────┬─────────────┘
└──────┬─────────────┘                 │
       │                                ▼
       ▼                      ┌────────────────────────┐
┌────────────────────┐         │   Embed Query          │
│   Chunking Engine  │         │   embedder.py          │
│   chunker.py       │         └──────────┬─────────────┘
└──────┬─────────────┘                    │
       │                                   ▼
       ▼                         ┌────────────────────────┐
┌────────────────────┐            │ Vector Search          │
│   Embedding Layer  │            │ InMemoryVectorStore    │
│   embedder.py      │            │ indexer.py             │
└──────┬─────────────┘            └──────────┬─────────────┘
       │                                      │
       ▼                                      ▼
┌────────────────────┐            ┌────────────────────────┐
│ Vector Indexer     │            │ Ranked Results         │
│ indexer.py         │            │ (tenant isolated)      │
└──────┬─────────────┘            └────────────────────────┘
       │
       ▼
┌────────────────────┐
│ Document Registry  │
│ registry.py        │
└────────────────────┘

Cross-cutting concerns (applied everywhere):
- Typed Errors (errors.py)
- Metrics (metrics.py)
- Structured Logging
- Tenant Isolation
- Deterministic IDs

================================================================================
SYSTEM OVERVIEW
================================================================================

The system is a production-grade Retrieval-Augmented Generation (RAG) backend with:

- Deterministic ingestion
- Idempotent indexing
- Typed failures
- Tenant isolation
- Query caching
- Metrics and observability
- Strong test coverage

The architecture is intentionally explicit, layered, and replaceable.

================================================================================
INGESTION PIPELINE
================================================================================

File: ingestion_service/pipeline.py

Responsibilities:
- Orchestrates the full ingestion lifecycle
- Enforces idempotency
- Coordinates deletion and reindexing

Execution Flow:
1. Extract text and metadata
2. Compute SHA-256 hash
3. Check document registry
4. Chunk text deterministically
5. Embed chunks with retry
6. Index vectors
7. Register document version

Pipeline:
file
 → extract_text
 → chunk_text
 → embed_chunks
 → index_chunks
 → registry.register

Guarantees:
- Same document version is ingested once
- Partial failures never leave stale vectors
- Re-ingestion is safe and deterministic

================================================================================
TEXT EXTRACTION AND NORMALIZATION
================================================================================

File: ingestion_service/preprocess.py

Supported formats:
- .txt
- .docx
- .pdf (native extraction with OCR fallback)

Output contract:
{
  "text": "<normalized_text>",
  "metadata": {
      "sha256": "<file_hash>",
      "source": "<file_type>"
  }
}

Design notes:
- File type detection via extension
- Unsupported formats fail fast
- OCR logic is isolated
- Text normalization is explicit and testable

================================================================================
CHUNKING ENGINE
================================================================================

File: ingestion_service/chunker.py

Chunk identity:
chunk_id = SHA256(doc_id + file_sha256 + chunk_index)

Chunk fields:
- chunk_id
- doc_id
- sha256
- chunk_index
- char_start
- char_end
- text

Invariants:
- overlap < chunk_size
- No empty chunks
- No infinite loops
- Stable output for identical input

================================================================================
EMBEDDING LAYER
================================================================================

File: ingestion_service/embedder.py

Architecture:
chunks → embed_chunks → embedder.embed()

Features:
- Pluggable embedder interface
- Batch processing
- Exponential backoff retry
- Strict output validation

================================================================================
VECTOR INDEXING
================================================================================

File: ingestion_service/indexer.py

- Deterministic upserts
- Cosine similarity search
- Metadata-driven filtering
- Tenant-safe deletes

================================================================================
TENANT ISOLATION
================================================================================

- tenant_id stored in vector metadata
- Mandatory filter on every query
- Guaranteed data separation

================================================================================
RETRIEVAL AND CACHE
================================================================================

- Query embeddings cached
- Vector search cached
- Verified via mock-based tests

================================================================================
METRICS AND OBSERVABILITY
================================================================================

- Internal counters
- Replaceable backend
- No vendor lock-in

================================================================================
WHY THIS SYSTEM MATTERS
================================================================================

This is not a demo.
This is a **production-ready, test-hardened, enterprise-grade RAG system**.

================================================================================
FINAL NOTE
================================================================================

