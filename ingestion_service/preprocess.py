from pathlib import Path
from typing import Dict
import hashlib

from ingestion_service.errors import ExtractionError


def extract_text(file_path: Path) -> Dict:
    """
    Extract text from a document.
    Supports txt, docx, pdf (with OCR fallback).
    """
    if not file_path.exists():
        raise ExtractionError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    try:
        if suffix == ".txt":
            text = _extract_txt(file_path)
        elif suffix == ".docx":
            text = _extract_docx(file_path)
        elif suffix == ".pdf":
            text = _extract_pdf(file_path)
        else:
            raise ExtractionError(f"Unsupported file type: {suffix}")
    except Exception as exc:
        raise ExtractionError(str(exc)) from exc

    return {
        "text": _normalize(text),
        "metadata": {
            "source_file": file_path.name,
            "sha256": _sha256(file_path),
            "char_count": len(text),
        },
    }


def _extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_pdf(path: Path) -> str:
    text = _pdf_text(path)
    if len(text.strip()) < 50:
        text = _pdf_ocr(path)
    return text


def _pdf_text(path: Path) -> str:
    from pdfminer.high_level import extract_text

    try:
        return extract_text(str(path)) or ""
    except Exception:
        return ""


def _pdf_ocr(path: Path) -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        return ""

    chunks = []
    try:
        images = convert_from_path(str(path))
        for img in images:
            txt = pytesseract.image_to_string(img)
            if txt:
                chunks.append(txt)
    except Exception:
        return ""

    return "\n".join(chunks)


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read())
    return h.hexdigest()
