from ingestion_service.preprocess import extract_text, _extract_txt,_extract_docx,_extract_pdf,_pdf_text,_pdf_ocr,_normalize,_sha256
import pytest 
from pathlib import Path
import ingestion_service.preprocess as preprocess

import tempfile

# Test extract_text with txt, docx, and pdf with and without OCR
def create_temp_file(tmp_path, content, suffix):
    p = tmp_path / f"sample{suffix}"
    if suffix == ".txt":
        p.write_text(content, encoding="utf-8")
    elif suffix == ".docx":
        from docx import Document
        doc = Document()
        doc.add_paragraph(content)
        doc.save(str(p))
    elif suffix == ".pdf":
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)
        pdf.output(str(p))
    return p

@pytest.mark.parametrize("suffix", [".txt", ".docx", ".pdf"])
def test_extract_text_various_suffixes(tmp_path, suffix):
    content = "This is a test document. \nWith multiple lines."
    p = create_temp_file(tmp_path, content, suffix)
    result = extract_text(p)
    assert "text" in result
    assert "document" in result["text"]
    assert "metadata" in result
    assert result["metadata"]["source_file"] == p.name
    assert isinstance(result["metadata"]["sha256"], str)
    assert result["metadata"]["char_count"] >= len(content)-1  # newlines may be normalized

def test_extract_text_file_not_found(tmp_path):
    fake_file = tmp_path / "nofile.txt"
    with pytest.raises(FileNotFoundError):
        extract_text(fake_file)

def test_extract_text_unsupported_type(tmp_path):
    p = tmp_path / "sample.xyz"
    p.write_text("dummy", encoding="utf-8")
    with pytest.raises(ValueError):
        extract_text(p)

def test__extract_txt(tmp_path):
    content = "Simple text file."
    p = tmp_path / "t.txt"
    p.write_text(content, encoding="utf-8")
    assert _extract_txt(p) == content

def test__extract_docx(tmp_path):
    try:
        from docx import Document
    except ImportError:
        pytest.skip("python-docx not installed")
    content = "Docx content one.\nDocx content two."
    docx_path = tmp_path / "t.docx"
    from docx import Document
    doc = Document()
    doc.add_paragraph("Docx content one.")
    doc.add_paragraph("Docx content two.")
    doc.save(str(docx_path))
    out = _extract_docx(docx_path)
    assert "Docx content one." in out and "Docx content two." in out

def test__extract_pdf(tmp_path):
    try:
        from fpdf import FPDF
    except ImportError:
        pytest.skip("fpdf not installed for PDF stub generation")
    content = "PDF content test for extraction."
    pdf_path = create_temp_file(tmp_path, content, ".pdf")
    out = _extract_pdf(pdf_path)
    # Should extract at least part of the original content
    assert "content" in out

@pytest.mark.parametrize("s", [
    "Hello    there \n my  friend!",
    "",
    "SingleWord",
    "Multiple    spaces  here"
])
def test__normalize(s):
    norm = _normalize(s)
    assert all(w for w in norm.split())  # no blank strings
    if s.strip():
        assert "  " not in norm
        # Word count not changed
        assert len(s.split()) == len(norm.split())
    else:
        assert norm == ""

def test__sha256(tmp_path):
    file_path = tmp_path / "test.bin"
    data = b"hash this"
    file_path.write_bytes(data)
    expected = __import__("hashlib").sha256(data).hexdigest()
    assert _sha256(file_path) == expected

def test__pdf_text_returns_string(tmp_path):
    try:
        from fpdf import FPDF
    except ImportError:
        pytest.skip("fpdf not installed")
    pdf_path = create_temp_file(tmp_path, "Testing pdfminer extraction.", ".pdf")
    out = _pdf_text(pdf_path)
    assert isinstance(out, str)

def test__pdf_ocr_runs_no_dependencies(tmp_path, monkeypatch):
    # Simulate missing dependencies
    pdf_path = tmp_path / "img.pdf"
    pdf_path.write_bytes(b"")  # Empty stub
    import sys
    modules = {}
    monkeypatch.setitem(sys.modules, "pytesseract", None)
    monkeypatch.setitem(sys.modules, "pdf2image", None)
    out = _pdf_ocr(pdf_path)
    assert out == ""  # Should gracefully degrade

# Note: To fully test OCR one would need tesseract installed + scan-like PDF sample.
