"""Conservative confidence score for document understanding."""
from __future__ import annotations
from typing import Any


def score(text: str, fields: dict[str, Any], ocr_details: dict[str, Any] | None = None) -> dict[str, Any]:
    checks = {
        "nonempty_text": bool((text or "").strip()),
        "subject": bool(fields.get("subject")),
        "authority": bool(fields.get("authority")),
        "reference_or_date": bool(fields.get("reference") or fields.get("date")),
    }
    value = sum(checks.values()) / len(checks)
    if ocr_details and ocr_details.get("level") == "LOW":
        value *= 0.7
    level = "HIGH" if value >= .8 else "MEDIUM" if value >= .5 else "LOW"
    return {"score": round(value, 2), "level": level, "checks": checks}
