from pathlib import Path
import logging

from ingestion_service.preprocess import extract_text
from ingestion_service.chunker import chunk_text
from ingestion_service.embedder import embed_chunks
from ingestion_service.indexer import index_chunks

logger = logging.getLogger(__name__)

def ingest_document(file_path:Path,doc_id:str,embedder,vector_store,chunk_size:int=1000,chunk_overlap:int=200,) -> int :
    """
    End to end ingestion pipeline.
    Steps:
    1. Extract + normalize text
    2. Chunk deterministicly
    3. Generate embeddings
    4. Index chunks
    
    Args:
    file_path: Path to the document to ingest
    doc_id: ID of the document
    embedder: Embedder to use
    vector_store: Vector store to use
    chunk_size: Size of each chunk
    chunk_overlap: Overlap between chunks
    
    Returns:
    Number of chunks ingested

    Raises:
    Any exceptions from embedding layers
    """

    logger.info(
        "Ingesting document",
        extra={"file": str(file_path), "file_id": doc_id},
    )
    
    # 1. Preprocess 
    extracted = extract_text(file_path)
    text = extracted["text"]
    metadata = extracted["metadata"]

    # 2. Chunk
    chunks = chunk_text(text = text,
    chunk_size = chunk_size,
    overlap = chunk_overlap,
    doc_id = doc_id,
    sha256 = metadata["sha256"],
    )
    
    if not chunks:
        logger.warning(
            "No chunks generated skipping ingestion of index",
            extra={"file": str(file_path), "file_id": doc_id},
        )

        return 0

    # 3. Embd
    chunks = embed_chunks(chunks=chunks,embedder=embedder)

    # 4. Index
    index_chunks(chunks=chunks,vector_store=vector_store)

    logger.info(
        "Document ingested",
        extra={"file": str(file_path), "file_id": doc_id},
    )

    return len(chunks)



    