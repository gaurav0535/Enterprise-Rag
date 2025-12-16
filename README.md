# Enterprise RAG – Ingestion Service

This service is the entry point for an enterprise-grade Retrieval-Augmented Generation (RAG) platform.

Its responsibility is to accept documents, persist them safely, and enqueue them for downstream processing (text extraction, chunking, embedding, indexing).

⚠️ This service does NOT perform chunking, embedding, or indexing. Those are handled by downstream workers.

---

## What this service does
- Accepts document uploads via HTTP API
- Persists uploaded files to storage
- Generates a unique job_id per ingestion request
- Returns a deterministic ingestion response
- Logs ingestion events in structured form

---

## What this service does NOT do
- Text extraction
- OCR
- Chunking
- Embeddings
- Vector database operations
- Background processing

These concerns are intentionally separated for enterprise scalability.

---

## Tech Stack
- Python
- FastAPI
- Uvicorn
- Pydantic

---

## Project Structure
