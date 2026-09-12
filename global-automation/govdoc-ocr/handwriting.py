"""Handwriting evidence contract.

This module intentionally does not claim handwriting recognition. It marks
regions that need human/vision review when backend confidence indicates
uncertainty.
"""
from __future__ import annotations

def review_flags(regions: list[dict], *, confidence_threshold: float = 0.65) -> list[dict]:
    flags=[]
    for region in regions:
        confidence=region.get("confidence")
        uncertain = confidence is not None and float(confidence) < confidence_threshold
        if uncertain:
            flags.append({"region_id": region.get("id"), "reason": "low_ocr_confidence", "requires_review": True})
    return flags

def handwriting_status(*, backend: str | None, regions: list[dict]) -> dict:
    """Return honest capability status without guessing handwritten text."""
    flags=review_flags(regions)
    return {"supported": False, "recognized": False, "backend": backend, "requires_review": bool(flags), "review_flags": flags}
