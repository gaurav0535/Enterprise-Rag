# query_service/dependencies.py
from ingestion_service.embedder import MockEmbedder
from ingestion_service.indexer import InMemoryVectorStore
from ingestion_service.retriever import Retriever


# TEMP: same store as ingestion for local use
embedder = MockEmbedder()
vector_store = InMemoryVectorStore()

retriever = Retriever(embedder, vector_store)
