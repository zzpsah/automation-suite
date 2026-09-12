"""Dependency-free checks for GovDOC OCR release readiness."""
from __future__ import annotations

REQUIRED_RESULT_KEYS = ("schema_version", "text", "normalized_text", "filename", "pages", "ocr")


def validate_result(result: dict) -> dict:
    missing = [key for key in REQUIRED_RESULT_KEYS if key not in result]
    pages = result.get("pages", [])
    page_numbers = [p.get("page_number") for p in pages]
    nonempty_pages = bool(page_numbers)
    sequential = nonempty_pages and page_numbers == list(range(1, len(page_numbers) + 1))
    return {
        "valid": not missing and sequential,
        "missing_keys": missing,
        "nonempty_pages": nonempty_pages,
        "sequential_pages": sequential,
        "page_count": len(page_numbers),
        "checks": {"required_keys": not missing, "nonempty_pages": nonempty_pages, "page_order": sequential},
    }
