"""Dependency-free checks for GovDOC OCR release readiness."""
from __future__ import annotations

REQUIRED_RESULT_KEYS = ("schema_version", "text", "normalized_text", "filename", "pages", "ocr")


def validate_result(result: dict) -> dict:
    missing = [key for key in REQUIRED_RESULT_KEYS if key not in result]
    page_numbers = [p.get("page_number") for p in result.get("pages", [])]
    sequential = page_numbers == list(range(1, len(page_numbers) + 1))
    return {
        "valid": not missing and sequential,
        "missing_keys": missing,
        "sequential_pages": sequential,
        "page_count": len(page_numbers),
        "checks": {"required_keys": not missing, "page_order": sequential},
    }
