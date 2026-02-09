import sys
import threading
import time
from ingestion_service.chunker import chunk_text

def run_chunker():
    text = "a" * 1200
    print("Starting chunking...")
    # chunk_size=1000, overlap=200. text_len=1200.
    # Iter 1: start=0, end=1000. next_start=800.
    # Iter 2: start=800, end=1200. next_start=1000.
    # Iter 3: start=1000, end=1200. next_start=1000. -> INFINITE LOOP
    chunk_text(text, "doc1", "sha1", chunk_size=1000, overlap=200)
    print("Finished chunking")

t = threading.Thread(target=run_chunker)
t.daemon = True
t.start()
t.join(timeout=5)

if t.is_alive():
    print("Chunking timed out - INFINITE LOOP DETECTED")
else:
    print("Chunking completed")
