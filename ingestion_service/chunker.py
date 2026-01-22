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

    if overlap >= chunk_size:
        raise ChunkingError("overlap must be smaller than chunk_size")

    if not text:
        return []

    chunks = []
    text_length = len(text)
    start = 0
    index = 0

    # If text fits in one chunk → return exactly one
    if text_length <= chunk_size:
        return [{
            "chunk_id": _chunk_id(doc_id, sha256, 0),
            "chunk_index": 0,
            "text": text,
            "char_start": 0,
            "char_end": text_length,
            "doc_id": doc_id,
            "sha256": sha256,
        }]

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunks.append({
            "chunk_id": _chunk_id(doc_id, sha256, index),
            "chunk_index": index,
            "text": text[start:end],
            "char_start": start,
            "char_end": end,
            "doc_id": doc_id,
            "sha256": sha256,
        })

        index += 1
        start = end - overlap

        if start >= text_length:
            break

    return chunks


def _chunk_id(doc_id: str, sha256: str, index: int) -> str:
    raw = f"{doc_id}:{sha256}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()
