# ingestion_service/preprocess.py

from pathlib import Path
from typing import Dict
import hashlib
import logging

logger = logging.getLogger(__name__)


def extract_text(file_path: Path) -> Dict:
    """
    Extract clean text from a document.

    Supported formats:
    - .txt
    - .docx
    - .pdf (with OCR fallback)

    Returns:
        {
            "text": str,
            "metadata": {
                "source_file": str,
                "sha256": str,
                "char_count": int
            }
        }

    Raises:
        FileNotFoundError
        ValueError (unsupported file type)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        raw_text = _extract_txt(file_path)
    elif suffix == ".docx":
        raw_text = _extract_docx(file_path)
    elif suffix == ".pdf":
        raw_text = _extract_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    normalized_text = _normalize(raw_text)

    if not normalized_text:
        logger.warning(
            "Extracted empty text",
            extra={"file": str(file_path), "type": suffix},
        )

    return {
        "text": normalized_text,
        "metadata": {
            "source_file": file_path.name,
            "sha256": _sha256(file_path),
            "char_count": len(normalized_text),
        },
    }


def _extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(path)
    return "\n".join(
        p.text for p in doc.paragraphs if p.text.strip()
    )


def _extract_pdf(path: Path) -> str:
    """
    Attempt native PDF extraction first.
    Fallback to OCR if extracted text is insufficient.
    """
    text = _pdf_text(path)

    if len(text.strip()) < 50:
        logger.info(
            "Native PDF extraction insufficient, falling back to OCR",
            extra={"file": str(path)},
        )
        text = _pdf_ocr(path)

    return text


def _pdf_text(path: Path) -> str:
    from pdfminer.high_level import extract_text

    try:
        return extract_text(str(path)) or ""
    except Exception as exc:
        logger.warning(
            "Native PDF extraction failed",
            extra={"file": str(path), "error": str(exc)},
        )
        return ""


def _pdf_ocr(path: Path) -> str:
    """
    OCR fallback for scanned PDFs.
    Requires Tesseract installed on the system.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        logger.warning("OCR dependencies not installed")
        return ""

    text_chunks = []

    try:
        images = convert_from_path(str(path))
        for img in images:
            text = pytesseract.image_to_string(img)
            if text:
                text_chunks.append(text)
    except Exception as exc:
        logger.error(
            "OCR extraction failed",
            extra={"file": str(path), "error": str(exc)},
        )
        return ""

    return "\n".join(text_chunks)


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read())
    return h.hexdigest()
