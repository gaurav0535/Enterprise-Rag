#Chunking logic

from typing import List,Dict

import hashlib

def chunk_text(
    text : str,
    doc_id:str,
    sha256:str,
    chunk_size :int = 1000,
    overlap :int = 200,) -> List[Dict] :

    """Split text into overlapping chunks with deterministic IDs"""

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    index = 0
    text_length = len(text)

    while start < text_length:
        end =min(start+chunk_size , text_length)

        chunk_text = text [start:end]

        chunk_id = _chunk_id(doc_id,sha256,index)

        chunks.append({
            "chunk_id":chunk_id,
            "chunk_index":index,
            "text":chunk_text,
            "char_start":start,
            "char_end":end,
            "doc_id":doc_id,
            "sha256":sha256,
        })

        index += 1
        start = end - overlap

    return chunks

def _chunk_id(doc_id : str , sha256: str , index : int ) ->str:

    raw = f"{doc_id}:{sha256}:{index}"

    return hashlib.sha256(raw.encode()).hexdigest()  
  
