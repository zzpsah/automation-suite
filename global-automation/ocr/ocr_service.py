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
from .subject_extractor import extract_multiline_subject

OCR_SERVICE_VERSION = "1.1"


def process_pdf(pdf_path: str, work_dir: str, *, min_embedded_chars: int = 80) -> dict[str, Any]:
    """Extract document text and Sarkari metadata from a PDF."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(pdf_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("process_pdf currently accepts PDF files only")

    text, method = extract_document_text(str(path), work_dir, min_embedded_chars=min_embedded_chars)
    metadata = extract_metadata(text)
    result = asdict(metadata)
    subject = extract_multiline_subject(text)
    if subject:
        result["subject"] = subject
    result.update({
        "text": text,
        "extraction_method": method,
        "filename": path.name,
        "ocr_service_version": OCR_SERVICE_VERSION,
    })
    return result


def process_file(file_path: str, work_dir: str, *, min_embedded_chars: int = 80) -> dict[str, Any]:
    """Stable generic entry point for future consumers."""
    return process_pdf(file_path, work_dir, min_embedded_chars=min_embedded_chars)
