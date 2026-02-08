# ingestion_service/chunker.py

from typing import List, Dict
import hashlib
import logging
from ingestion_service.errors import ChunkingError

logger = logging.getLogger(__name__)


def _chunk_id(doc_id: str, sha256: str, index: int) -> str:
    raw = f"{doc_id}:{sha256}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()


# 

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

    text_len = len(text)

    # SHORT TEXT → SINGLE CHUNK
    if text_len <= chunk_size:
        return [{
            "chunk_id": _chunk_id(doc_id, sha256, 0),
            "doc_id": doc_id,
            "sha256": sha256,
            "chunk_index": 0,
            "char_start": 0,
            "char_end": text_len,
            "text": text,
        }]

    chunks = []
    start = 0
    index = 0
    step = chunk_size - overlap

    while start < text_len:
        end = min(start + chunk_size, text_len)

        chunks.append({
            "chunk_id": _chunk_id(doc_id, sha256, index),
            "doc_id": doc_id,
            "sha256": sha256,
            "chunk_index": index,
            "char_start": start,
            "char_end": end,
            "text": text[start:end],
        })

        index += 1
        start += step

    return chunks
