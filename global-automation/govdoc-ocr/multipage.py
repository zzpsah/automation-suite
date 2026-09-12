"""Storage-neutral multipage OCR consistency helpers."""
from __future__ import annotations


def summarize_pages(pages: list[dict]) -> dict:
    methods = [p.get("extraction_method") for p in pages]
    backends = [p.get("backend") for p in pages if p.get("backend")]
    return {
        "page_count": len(pages),
        "methods": methods,
        "ocr_pages": sum(m.startswith("ocr:") for m in methods if isinstance(m, str)),
        "embedded_pages": methods.count("embedded-text"),
        "backends": sorted(set(backends)),
        "mixed_processing": len(set(methods)) > 1,
        "signals": {"has_pages": bool(pages), "mixed_processing": len(set(methods)) > 1},
    }
