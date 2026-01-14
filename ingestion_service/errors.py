class IngestionError(Exception):
    """Base class for ingestion errors."""

class ExtractionError(IngestionError):
    """Raised when document extraction fails."""

class EmbeddingError(IngestionError):
    """Raised when embedding generation fails."""

class ChunkingError(IngestionError):
    """Raised when chunking fails."""

class IndexingError(IngestionError):
    """Raised when indexing fails."""

class RetrievalError(IngestionError):
    """Raised when retrieval fails."""

