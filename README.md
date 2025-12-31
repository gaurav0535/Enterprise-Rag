# Enterprise RAG – Ingestion Service

This service is the entry point for an enterprise-grade Retrieval-Augmented Generation (RAG) platform.

Its responsibility is to accept documents, persist them safely, and process them through text extraction, chunking, and preparation for downstream embedding and indexing.

---

## Features

### Core Functionality
- **Document Upload API**: Accepts document uploads via HTTP API
- **File Persistence**: Safely stores uploaded files with unique job IDs
- **Text Extraction**: Extracts text from multiple file formats (TXT, DOCX, PDF)
- **OCR Support**: Automatic OCR fallback for scanned PDFs
- **Text Chunking**: Splits documents into overlapping chunks for efficient processing
- **Metadata Generation**: Creates SHA256 hashes and metadata for all documents

### Supported File Formats
- **TXT**: Plain text files
- **DOCX**: Microsoft Word documents
- **PDF**: Portable Document Format (with OCR fallback for scanned documents)

---

## Tech Stack
- **Python 3.13+**
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation using Python type annotations
- **pdfminer.six**: PDF text extraction
- **python-docx**: DOCX file processing
- **pytesseract**: OCR for scanned PDFs
- **pytest**: Testing framework

---

## Project Structure

```
EnterpriseProject/
├── ingestion_service/
│   ├── __init__.py          # Package initialization
│   ├── app.py               # FastAPI application and routes
│   ├── config.py            # Configuration (storage paths)
│   ├── models.py            # Pydantic models/schemas
│   ├── preprocess.py        # Text extraction and OCR
│   ├── chunker.py           # Text chunking logic
│   ├── embedder.py          # Embedding module (placeholder)
│   ├── indexer.py           # Vector DB client (placeholder)
│   ├── workers.py           # Background job processing (placeholder)
│   ├── storage/             # Uploaded file storage directory
│   └── tests/
│       ├── conftest.py      # Pytest configuration
│       ├── test_preprocess.py  # Tests for text extraction
│       ├── test_chunker.py     # Tests for chunking
│       ├── test_embedder.py    # Tests for embedding (placeholder)
│       └── test_indexer.py     # Tests for indexing (placeholder)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Install Tesseract OCR** (for PDF OCR support):
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

---

## Usage

### Running the API Server

Start the FastAPI server:

```bash
uvicorn ingestion_service.app:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### `GET /health`
Health check endpoint.

**Response**:
```json
{
  "status": "ok"
}
```

#### `POST /ingest`
Upload a document for processing.

**Request**: Multipart form data with a file

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "file_name": "document.pdf"
}
```

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@/path/to/document.pdf"
```

### Using the Text Extraction Module

```python
from pathlib import Path
from ingestion_service.preprocess import extract_text

# Extract text from a file
file_path = Path("document.pdf")
result = extract_text(file_path)

print(result["text"])  # Extracted text
print(result["metadata"]["sha256"])  # File hash
print(result["metadata"]["char_count"])  # Character count
```

### Using the Chunking Module

```python
from ingestion_service.chunker import chunk_text

text = "Your long document text here..."
doc_id = "doc-123"
sha256 = "abc123def456..."

chunks = chunk_text(
    text=text,
    doc_id=doc_id,
    sha256=sha256,
    chunk_size=1000,  # Characters per chunk
    overlap=200       # Overlap between chunks
)

for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}: {chunk['text'][:50]}...")
```

---

## Module Documentation

### `preprocess.py` - Text Extraction

Main function: `extract_text(file_path: Path) -> Dict`

Extracts text from supported file formats and returns:
- `text`: Normalized extracted text
- `metadata`: Dictionary containing:
  - `source_file`: Original filename
  - `sha256`: SHA256 hash of the file
  - `char_count`: Character count of extracted text

**Features**:
- Automatic format detection based on file extension
- PDF native text extraction with OCR fallback
- Text normalization (whitespace cleanup)
- SHA256 hashing for file integrity

### `chunker.py` - Text Chunking

Main function: `chunk_text(text: str, doc_id: str, sha256: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]`

Splits text into overlapping chunks with:
- Deterministic chunk IDs based on document ID, SHA256, and index
- Configurable chunk size and overlap
- Metadata preservation (doc_id, sha256, position indices)

**Returns**: List of chunk dictionaries with:
- `chunk_id`: Unique identifier for the chunk
- `chunk_index`: Sequential index
- `text`: Chunk text content
- `char_start`: Start position in original text
- `char_end`: End position in original text
- `doc_id`: Source document ID
- `sha256`: Source document hash

### `models.py` - Pydantic Schemas

- `IngestResponse`: Response model for `/ingest` endpoint
- `HealthResponse`: Response model for `/health` endpoint

### `config.py` - Configuration

- `BASE_DIR`: Base directory of the ingestion service
- `STORAGE_DIR`: Directory for storing uploaded files (auto-created)

---

## Testing

The project uses **pytest** for testing. Tests are located in `ingestion_service/tests/`.

### Running Tests

From the project root:

```bash
python -m pytest
```

For verbose output:

```bash
python -m pytest -v
```

For specific test file:

```bash
python -m pytest ingestion_service/tests/test_preprocess.py
```

### Test Coverage

- **`test_preprocess.py`**: Comprehensive tests for text extraction
  - TXT file extraction
  - DOCX file extraction
  - PDF extraction (native and OCR)
  - Error handling (missing files, unsupported formats)
  - SHA256 hashing
  - Text normalization

- **`test_chunker.py`**: Tests for chunking functionality
  - Basic chunking with overlap
  - Edge cases (short text, overlap validation)
  - Chunk metadata correctness

### Test Configuration

The `conftest.py` file ensures proper import paths for tests, allowing pytest to discover and run tests regardless of the current working directory.

---

## Development

### Adding New File Format Support

1. Add extraction function in `preprocess.py`:
   ```python
   def _extract_xyz(path: Path) -> str:
       # Your extraction logic
       return extracted_text
   ```

2. Add format handling in `extract_text()`:
   ```python
   elif suffix == ".xyz":
       text = _extract_xyz(file_path)
   ```

3. Add tests in `test_preprocess.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Include docstrings for public functions
- Keep functions focused and single-purpose

---

## Dependencies

Key dependencies (see `requirements.txt` for complete list):

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `pdfminer.six`: PDF text extraction
- `python-docx`: DOCX processing
- `pytesseract`: OCR support
- `pytest`: Testing framework

---

## Future Enhancements

Planned modules (currently placeholders):
- **`embedder.py`**: Generate embeddings for text chunks
- **`indexer.py`**: Store embeddings in vector database
- **`workers.py`**: Background job processing

---

## License

[Add your license information here]

---

## Contributing

[Add contribution guidelines here]
