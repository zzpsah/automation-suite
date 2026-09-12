"""Deterministic synthetic PDF fixtures for page-routing and OCR smoke coverage."""
from __future__ import annotations

import io
import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont

from govdoc_ocr import process_pdf_bytes


def _embedded_pdf(text: str) -> bytes:
    """Build a tiny valid PDF containing selectable text without extra deps."""
    stream = f"BT /F1 16 Tf 72 720 Td ({text}) Tj ET".encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{number} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)


def _scanned_pdf() -> bytes:
    image = Image.new("RGB", (1400, 500), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=42)
    draw.text((80, 170), "GOVDOC OCR SCANNED NOTICE 2026", fill="black", font=font)
    draw.text((80, 250), "Hindi English Document", fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PDF", resolution=150.0)
    return buffer.getvalue()


def _merge_pdfs(first: bytes, second: bytes) -> bytes:
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for payload in (first, second):
        for page in PdfReader(io.BytesIO(payload)).pages:
            writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


EMBEDDED_TEXT = (
    "Government notice subject reference 2026 with sufficient selectable text "
    "to exercise the embedded-text routing contract without OCR."
)


def test_embedded_pdf_uses_embedded_page_path():
    result = process_pdf_bytes(_embedded_pdf(EMBEDDED_TEXT), "embedded-fixture.pdf")
    assert len(result["pages"]) == 1
    assert result["pages"][0]["extraction_method"] == "embedded-text"
    assert "Government notice" in result["pages"][0]["text"]


@pytest.mark.skipif(shutil.which("pdftoppm") is None or shutil.which("tesseract") is None, reason="OCR system tools unavailable")
def test_scanned_pdf_uses_ocr_page_path():
    result = process_pdf_bytes(_scanned_pdf(), "scanned-fixture.pdf")
    assert len(result["pages"]) == 1
    assert result["pages"][0]["extraction_method"].startswith("ocr:")
    assert result["pages"][0]["text"].strip()


@pytest.mark.skipif(shutil.which("pdftoppm") is None or shutil.which("tesseract") is None, reason="OCR system tools unavailable")
def test_mixed_pdf_preserves_page_order_and_routes_per_page():
    payload = _merge_pdfs(_embedded_pdf(EMBEDDED_TEXT), _scanned_pdf())
    result = process_pdf_bytes(payload, "mixed-fixture.pdf")
    assert [page["page"] for page in result["pages"]] == [1, 2]
    assert result["pages"][0]["extraction_method"] == "embedded-text"
    assert result["pages"][1]["extraction_method"].startswith("ocr:")
    assert "Government notice" in result["pages"][0]["text"]
    assert result["pages"][1]["text"].strip()
