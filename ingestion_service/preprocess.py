# ingestion_service/preprocess.py

from pathlib import Path
import hashlib


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _normalize(text: str) -> str:
    return " ".join(text.split())

def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except ImportError:
        # Fallback if pypdf is not installed, or try pdfminer if preferred
        import pdfminer.high_level
        return pdfminer.high_level.extract_text(str(path))

def _pdf_ocr(path: Path) -> str:
    import pytesseract
    from pdf2image import convert_from_path
    
    images = convert_from_path(str(path))
    text = []
    for img in images:
        text.append(pytesseract.image_to_string(img))
    return "\n".join(text)


def extract_text(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        text = _normalize(file_path.read_text(encoding="utf-8"))
    elif suffix == ".docx":
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    elif suffix == ".pdf":
        text = _pdf_text(file_path)
        if len(text.strip()) < 50:
             try:
                 text = _pdf_ocr(file_path)
             except Exception as e:
                 pass # keep original text if OCR fails
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return {
        "text": text,
        "metadata": {
            "sha256": _sha256(file_path),
            "source_file": file_path.name,
            "char_count": len(text)
        },
    }
