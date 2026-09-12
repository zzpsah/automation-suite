"""Reusable OCR engine for Hindi/English government documents."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .correction import correct_ocr_text


def extract_embedded_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF without OCR when useful."""
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    return correct_ocr_text("\n".join(page.extract_text() or "" for page in reader.pages))


def tesseract_available() -> bool:
    try:
        subprocess.run(["tesseract", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def ocr_image(image_path: str, lang: str = "hin+eng", psm: int = 6) -> str:
    """Run Tesseract and return corrected OCR text."""
    if not tesseract_available():
        raise RuntimeError("Tesseract is not installed or unavailable")
    result = subprocess.run(
        ["tesseract", image_path, "stdout", "-l", lang, "--psm", str(psm)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return correct_ocr_text(result.stdout)


def render_pdf(pdf_path: str, output_dir: str, dpi: int = 250) -> list[str]:
    """Render PDF pages to JPEG files using pdftoppm."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / "page"
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-jpeg", pdf_path, str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [str(p) for p in sorted(out.glob("page-*.jpg"))]


def extract_document_text(pdf_path: str, work_dir: str, min_embedded_chars: int = 80) -> tuple[str, str]:
    """Prefer embedded text; fall back to Hindi+English Tesseract OCR."""
    embedded = extract_embedded_pdf_text(pdf_path)
    if len("".join(embedded.split())) >= min_embedded_chars:
        return embedded, "embedded-text"

    pages = render_pdf(pdf_path, work_dir)
    text = "\n\n".join(ocr_image(page) for page in pages)
    return correct_ocr_text(text), "tesseract-hin+eng"
