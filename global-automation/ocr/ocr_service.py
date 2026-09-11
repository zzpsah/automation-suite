"""Stable, project-agnostic entry point for the Global OCR engine.

Consumers should depend on this module instead of coupling themselves to
Telegram, Supabase, B2, Google Drive, or a specific document processor.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .ocr_engine import extract_document_text
from .sarkari_normalizer import extract_metadata


def process_pdf(pdf_path: str, work_dir: str) -> dict:
    """Extract text and Sarkari metadata from any PDF.

    This function has no network/storage dependency and can therefore be
    reused by school portals, scanning tools, archive systems, desktop tools,
    batch jobs, and future OCR backends.
    """
    text, method = extract_document_text(pdf_path, work_dir)
    metadata = extract_metadata(text)
    result = asdict(metadata)
    result.update({
        "text": text,
        "extraction_method": method,
        "filename": Path(pdf_path).name,
    })
    return result
