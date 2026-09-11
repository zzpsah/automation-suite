"""Stable, project-agnostic public interface for Global Sarkari OCR.

Consumers should use this module instead of importing internal OCR engine
functions directly. It intentionally has no storage, database, Telegram, or
school-specific dependency.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .ocr_engine import extract_document_text
from .sarkari_normalizer import extract_metadata

OCR_SERVICE_VERSION = "1.0"


def process_pdf(
    pdf_path: str,
    work_dir: str,
    *,
    min_embedded_chars: int = 80,
) -> dict[str, Any]:
    """Extract document text and Sarkari metadata from a PDF.

    The result is deliberately independent of Supabase, Telegram, B2,
    Google Drive, or any consuming application's database schema.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(pdf_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("process_pdf currently accepts PDF files only")

    text, method = extract_document_text(
        str(path), work_dir, min_embedded_chars=min_embedded_chars
    )
    metadata = extract_metadata(text)
    result = asdict(metadata)
    result.update({
        "text": text,
        "extraction_method": method,
        "filename": path.name,
        "ocr_service_version": OCR_SERVICE_VERSION,
    })
    return result


def process_file(
    file_path: str,
    work_dir: str,
    *,
    min_embedded_chars: int = 80,
) -> dict[str, Any]:
    """Stable generic entry point for future consumers.

    PDF is the first supported document type. Additional formats/backends can
    be added behind this function without forcing downstream projects to
    change their integration contract.
    """
    return process_pdf(
        file_path,
        work_dir,
        min_embedded_chars=min_embedded_chars,
    )
