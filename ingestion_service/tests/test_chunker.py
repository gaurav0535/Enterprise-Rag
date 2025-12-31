from ingestion_service.chunker import chunk_text
import pytest

def test_chunk_test_basic():
    # This test checks that chunk_test correctly splits a string into overlapping chunks.
    # Create a string of 1040 characters by repeating the alphabet.
    text = "abcdefghijklmnopqrstuvwxyz" * 40  # len=1040
    doc_id = "doc123"
    sha256 = "abc123"
    chunk_size = 500   # Each chunk will be up to 500 characters
    overlap = 100      # Each chunk (except the first) should overlap the previous by 100 chars

    chunks = chunk_text(text, doc_id=doc_id, sha256=sha256, chunk_size=chunk_size, overlap=overlap)

    # With 1040 chars, chunk_size=500, overlap=100:
    # 1st chunk: 0-499 (chars 0-499)
    # 2nd chunk: 400-899 (chars 400-899, starts 100 before end of previous chunk)
    # 3rd chunk: 800-1039 (chars 800 to end)
    assert len(chunks) == 3

    # Check start and end positions for each chunk
    assert chunks[0]["char_start"] == 0
    assert chunks[0]["char_end"] == 500
    assert chunks[1]["char_start"] == 400
    assert chunks[1]["char_end"] == 900
    assert chunks[2]["char_start"] == 800
    assert chunks[2]["char_end"] == 1040

    # Check that each chunk contains the correct metadata and text
    for i, chunk in enumerate(chunks):
        # The doc_id and sha256 should be preserved
        assert chunk["doc_id"] == doc_id
        assert chunk["sha256"] == sha256
        # The chunk index should be strictly increasing and match the loop index
        assert chunk["chunk_index"] == i
        # The chunk_id should be a string (the actual calculation is tested in unit tests elsewhere)
        assert isinstance(chunk["chunk_id"], str)
        # The text field should exactly match the corresponding slice of the original string
        assert chunk["text"] == text[chunk["char_start"]:chunk["char_end"]]

def test_chunk_test_overlap_gt_size():
    # This test verifies that chunk_test raises an error if overlap is >= chunk_size.
    text = "testtext"
    # overlap > chunk_size should cause function to raise ValueError
    with pytest.raises(ValueError):
        chunk_text(text, doc_id="d", sha256="h", chunk_size=100, overlap=200)

def test_chunk_test_short_text():
    # This test checks that if the input text is shorter than the chunk_size, a single chunk is returned.
    text = "short"
    # chunk_size > len(text) so should return exactly one chunk with full text
    chunks = chunk_text(text, doc_id="d", sha256="h", chunk_size=10, overlap=3)
    assert len(chunks) == 1
    # The single chunk's text should be the original string
    assert chunks[0]["text"] == text
    # char_start should be 0, char_end should be length of the string
    assert chunks[0]["char_start"] == 0
    assert chunks[0]["char_end"] == len(text)


