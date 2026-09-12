"""Validation helpers for dates and government-document metadata."""
from __future__ import annotations
import re
from datetime import date

_DATE_PATTERNS = (
    re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"),
    re.compile(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b"),
)


def extract_date_candidates(text: str) -> list[dict]:
    """Return syntactic date candidates with validity status; never normalize silently."""
    out = []
    for pattern in _DATE_PATTERNS:
        for m in pattern.finditer(text or ""):
            values = tuple(int(x) for x in m.groups())
            if pattern is _DATE_PATTERNS[0]:
                d, mo, y = values
            else:
                y, mo, d = values
            valid = True
            try:
                date(y, mo, d)
            except ValueError:
                valid = False
            out.append({"text": m.group(0), "start": m.start(), "end": m.end(), "valid_calendar_date": valid})
    return out


def validate_metadata(text: str, metadata: dict | None = None) -> dict:
    candidates = extract_date_candidates(text or "")
    return {
        "date_candidates": candidates,
        "metadata_keys": sorted((metadata or {}).keys()),
        "signals": {"has_valid_date": any(c["valid_calendar_date"] for c in candidates), "has_invalid_date": any(not c["valid_calendar_date"] for c in candidates)},
        "evidence_only": True,
    }
