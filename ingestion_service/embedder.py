from typing import List , Dict

import time
import random

class EmbeddingError(Exception):
    pass

class BaseEmbedder:
    """
    Abstract embeding interface
    """

    def embed(self,texts:List[str]) -> List[List[float]]:
        raise NotImplementedError

class MockEmbedder(BaseEmbedder):
    """
    Deterministic mock
    """
    def embd(self, texts :List[str]) -> List[List[float]]:
        return [[float(len(t))] for t in texts]

class SimulatedRemoteEmbedder(BaseEmbedder):
    """
    Simulates a remote embedding service.
    """

    def embed(self,texts:List[str]) -> List[List[float]]:
        time.sleep(0.2)

        if random.random() < 0.1 :
            raise EmbeddingError("Transient embedding failure")

        return [[float(len(t))] * 3 for t in texts ]



def embed_chunks(chunks : List[Dict],embedder : BaseEmbedder,batch_size : int = 8,max_retries : int = 3,) -> List[Dict]:
    """
    Attach embeddings to chunk with batching and retry
    """

    texts = [c["text"] for c in chunks]

    embeddings = []

    for i in range(0,len(texts),batch_size):
        batch = texts[i:i + batch_size]
        retries = 0

        while True:
            try:
                batch_embeddings = embedder.embed(batch)
                embeddings.extend(batch_embeddings)
                break
            except EmbeddingError:
                retries +=1
                if retries >= max_retries:
                    raise
                time.sleep(2 ** retries)

    #Attach embeddings

    for chunk , emb in zip(chunks,embeddings):
        chunk["embeddings"] = emb

    return chunks



