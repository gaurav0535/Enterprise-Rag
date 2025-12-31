import pytest
from ingestion_service.embedder import (
    BaseEmbedder,
    MockEmbedder,
    SimulatedRemoteEmbedder,
    EmbeddingError,
    embed_chunks,
)

def test_mock_embedder():
    emb = MockEmbedder()
    inputs = ["abc", "de", ""]  # lens: 3, 2, 0
    result = emb.embd(inputs)
    assert result == [[3.0], [2.0], [0.0]]

def test_base_embedder_not_implemented():
    base = BaseEmbedder()
    with pytest.raises(NotImplementedError):
        base.embed(["sample"])

def test_simulated_remote_embedder_success(monkeypatch):
    emb = SimulatedRemoteEmbedder()
    # Patch random.random to ALWAYS avoid error for this test
    monkeypatch.setattr("random.random", lambda: 0.5)
    texts = ["foo", "barbaz"]
    result = emb.embed(texts)
    # Each embedding is a list of len 3, all elements == len(t)
    assert result == [[3.0, 3.0, 3.0], [6.0, 6.0, 6.0]]

def test_simulated_remote_embedder_transient(monkeypatch):
    emb = SimulatedRemoteEmbedder()
    # Patch random.random to simulate error first call, then success
    call_count = {"c": 0}
    def myrand():
        call_count["c"] += 1
        return 0.01 if call_count["c"] == 1 else 0.5
    monkeypatch.setattr("random.random", myrand)
    # Patch time.sleep to speed up test
    monkeypatch.setattr("time.sleep", lambda s: None)
    # If error is raised, embed_chunks will handle, but for direct call it should just raise
    with pytest.raises(EmbeddingError):
        emb.embed(["should-fail"])

def test_embed_chunks_batches(monkeypatch):
    # Use SimulatedRemoteEmbedder, monkeypatch to avoid sleep/random failures
    monkeypatch.setattr("random.random", lambda: 0.6)
    monkeypatch.setattr("time.sleep", lambda t: None)
    emb = SimulatedRemoteEmbedder()
    chunks = [
        {"text": "a"},
        {"text": "ab"},
        {"text": "abc"},
        {"text": "abcd"},
        {"text": "abcde"},
        {"text": "abcdef"},
        {"text": "abcdefg"},
        {"text": "abcdefgh"},
        {"text": "abcdefghi"},
    ]
    # batch_size=3, so should be 3 batches
    out = embed_chunks([c.copy() for c in chunks], emb, batch_size=3)
    # Each chunk must have 'embeddings' matching expected
    for orig, o in zip(chunks, out):
        l = float(len(orig["text"]))
        assert o["embeddings"] == [l, l, l]

def test_embed_chunks_retry_on_embedding_error(monkeypatch):
    chunk = {"text": "hello"}
    calls = {"embed": 0}
    class FailingEmbedder(BaseEmbedder):
        def embed(self, texts):
            if calls["embed"] < 2:
                calls["embed"] += 1
                raise EmbeddingError("fail")
            return [[42.0] for _ in texts]
    # Patch time.sleep to avoid actual sleep
    monkeypatch.setattr("time.sleep", lambda x: None)
    out = embed_chunks([chunk.copy()], FailingEmbedder(), batch_size=1, max_retries=3)
    assert out[0]["embeddings"] == [42.0]
    assert calls["embed"] == 2

def test_embed_chunks_retry_exceeds(monkeypatch):
    class AlwaysFailEmbedder(BaseEmbedder):
        def embed(self, texts):
            raise EmbeddingError("always fails")
    monkeypatch.setattr("time.sleep", lambda x: None)
    with pytest.raises(EmbeddingError):
        embed_chunks([{"text": "x"}], AlwaysFailEmbedder(), batch_size=1, max_retries=2)

