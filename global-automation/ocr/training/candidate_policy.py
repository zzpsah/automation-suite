"""Safety policy for promoting learned OCR vocabulary candidates."""
from __future__ import annotations

import re

DATE = re.compile(r"^\d{1,4}[./-]\d{1,2}[./-]\d{1,4}$")


def validate_candidate(observed: str, correction: str, *, frequency: int = 1) -> tuple[bool, str]:
    observed = (observed or "").strip()
    correction = (correction or "").strip()
    if not observed or not correction:
        return False, "empty-value"
    if len(observed) > 200 or len(correction) > 300:
        return False, "too-long"
    if DATE.match(observed) or DATE.match(correction):
        return False, "date-value"
    if frequency < 2:
        return False, "insufficient-frequency"
    if observed.casefold() == correction.casefold():
        return False, "unchanged"
    return True, "candidate"
