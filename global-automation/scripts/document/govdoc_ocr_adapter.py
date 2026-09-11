"""Bridge the production document processor to the shared GovDOC OCR Engine.

The existing processor remains the owner of intake/storage/Supabase/business rules.
This adapter only replaces its OCR and metadata functions, keeping a safe fallback
inside the processor if the shared engine raises an exception.
"""
from __future__ import annotations

import hashlib
from typing import Any

from govdoc_ocr.ocr_service import process_pdf_bytes

_CACHE: dict[str, dict[str, Any]] = {}


def _run(data: bytes, filename: str = "document.pdf") -> dict[str, Any]:
    key = hashlib.sha256(data).hexdigest()
    if key not in _CACHE:
        _CACHE[key] = process_pdf_bytes(data, filename)
    return _CACHE[key]


def install(processor_module) -> None:
    """Install GovDOC OCR hooks into the existing document processor."""
    original_embedded = processor_module.embedded_pdf_text
    original_ocr = processor_module.ocr_pdf
    original_metadata = processor_module.extract_metadata

    def embedded(data: bytes) -> str:
        try:
            result = _run(data)
            if result["extraction_method"] == "GovDOC OCR: embedded-text":
                return result["text"]
            return ""
        except Exception:
            return original_embedded(data)

    def ocr(data: bytes, workdir: str) -> str:
        try:
            return _run(data)["text"]
        except Exception:
            return original_ocr(data, workdir)

    def metadata(text: str, filename: str):
        for result in reversed(list(_CACHE.values())):
            if result.get("text") == text:
                return (
                    result.get("subject", ""), result.get("authority", ""),
                    result.get("reference_number", ""), result.get("issue_date", ""),
                    result.get("normalized_issue_date"), result.get("short_description", ""),
                    result.get("detailed_summary", ""), result.get("category_key", "other"),
                    result.get("category", "Other"), result.get("confidence", "MEDIUM"),
                )
        return original_metadata(text, filename)

    processor_module.embedded_pdf_text = embedded
    processor_module.ocr_pdf = ocr
    processor_module.extract_metadata = metadata
