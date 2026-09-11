"""Stable document processor API.

Consumers call one function. OCR, extraction and classification remain
replaceable internals.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ocr.core import process_file as ocr_process_file
from .classification import classify
from .confidence import score
from .extraction import extract
from .metadata import build_metadata
from .summarization import summarize

ENGINE_VERSION = "1.0.0"


def process(file_path: str, work_dir: str) -> dict[str, Any]:
    """Run the complete reusable OCR + document-understanding pipeline."""
    path = Path(file_path)
    ocr_result = ocr_process_file(str(path), work_dir)
    text = str(ocr_result.get("text", ""))
    fields = extract(text, ocr_result)
    metadata = build_metadata(path.name, ocr_result, fields)
    category = classify(text, ocr_result.get("category"))
    summary = summarize(text)
    confidence = score(text, fields, ocr_result.get("confidence_details"))
    return {
        "engine_version": ENGINE_VERSION,
        "ocr": ocr_result,
        "metadata": metadata,
        "classification": category,
        "summary": summary,
        "entities": fields.get("entities", {}),
        "confidence": confidence,
    }
