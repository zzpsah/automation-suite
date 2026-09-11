"""Deterministic scoring helpers for selecting an OCR image candidate."""
from __future__ import annotations

import re


def score_text(text: str) -> float:
    """Score OCR output without knowing ground truth.

    This is a selection heuristic only, never an accuracy claim. It rewards
    usable text, line structure and Hindi/English administrative characters,
    while penalizing obvious garbage/control-heavy output.
    """
    value = text or ""
    compact = "".join(value.split())
    if not compact:
        return 0.0
    useful = len(re.findall(r"[\u0900-\u097F\w]", compact, flags=re.UNICODE))
    controls = sum(ord(ch) < 32 and ch not in "\n\t\r" for ch in value)
    lines = len([line for line in value.splitlines() if line.strip()])
    score = min(len(compact) / 600.0, 1.0) * 0.55
    score += min(lines / 12.0, 1.0) * 0.20
    score += (useful / max(len(compact), 1)) * 0.25
    score -= min(controls / max(len(value), 1), 0.1)
    return round(max(0.0, min(1.0, score)), 4)
