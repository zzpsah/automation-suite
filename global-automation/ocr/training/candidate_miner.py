"""Mine conservative correction candidates from reviewed OCR pairs."""
from __future__ import annotations

from collections import Counter
import re


def _tokens(text: str) -> list[str]:
    return re.findall(r"[^\s,;:()]+", text or "")


def mine_token_corrections(records: list[dict], min_count: int = 3) -> list[dict]:
    """Find repeatable raw→corrected substitutions as review candidates."""
    pairs: Counter[tuple[str, str]] = Counter()
    for record in records:
        raw = _tokens(record.get("raw_text", ""))
        corrected = _tokens(record.get("corrected_text", ""))
        if len(raw) != len(corrected):
            continue
        for before, after in zip(raw, corrected):
            if before != after and before and after:
                pairs[(before, after)] += 1

    return [
        {
            "observed": before,
            "correction": after,
            "frequency": count,
            "review_status": "candidate",
            "source_type": "ocr_correction",
        }
        for (before, after), count in pairs.most_common()
        if count >= min_count
    ]
