"""Document field extraction built on OCR evidence, not invented values."""
from __future__ import annotations
import re
from typing import Any

DATE_RE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
REF_RE = re.compile(r"(?i)\b(?:memo|ref(?:erence)?|पत्रांक|ज्ञापांक|क्रमांक)\s*[:./-]?\s*([A-Z0-9][A-Z0-9./_-]{2,})")


def extract(text: str, ocr_result: dict[str, Any] | None = None) -> dict[str, Any]:
    result = dict(ocr_result or {})
    dates = DATE_RE.findall(text or "")
    refs = REF_RE.findall(text or "")
    return {
        "subject": result.get("subject"),
        "authority": result.get("authority") or (result.get("bihar_office") or {}).get("name"),
        "reference": result.get("reference_number") or (refs[0] if refs else None),
        "date": result.get("issue_date") or (dates[0] if dates else None),
        "entities": {
            "dates": dates,
            "references": refs,
        },
    }
