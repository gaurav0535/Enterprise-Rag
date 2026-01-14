# ingestion_service/chunker.py

from typing import List, Dict
import hashlib
import logging
from ingestion_service.errors import ChunkingError

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    doc_id: str,
    sha256: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> List[Dict]:
    """
    Split normalized text into overlapping chunks with deterministic IDs.

    Guarantees:
    - Deterministic output for same inputs
    - Stable chunk IDs across re-ingestion
    - No infinite loops
    - Overlap < chunk_size

    Returns:
        List of chunk dictionaries.
    """
    if not text:
        logger.warning(
            "Empty text received for chunking",
            extra={"doc_id": doc_id},
        )
        return []

    if overlap >= chunk_size:
        raise ChunkingError("overlap must be smaller than chunk_size")

    chunks = []
    text_length = len(text)

    start = 0
    index = 0

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunk_body = text[start:end].strip()
        if not chunk_body:
            break

        chunk_id = _chunk_id(doc_id, sha256, index)

        chunks.append({
            "chunk_id": chunk_id,
            "chunk_index": index,
            "text": chunk_body,
            "char_start": start,
            "char_end": end,
            "doc_id": doc_id,
            "sha256": sha256,
        })

        index += 1

        # Prevent infinite loop
        next_start = end - overlap
        if next_start <= start:
            break

        start = next_start

    return chunks


def _chunk_id(doc_id: str, sha256: str, index: int) -> str:
    """
    Generate a deterministic chunk ID.
    """
    raw = f"{doc_id}:{sha256}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()
