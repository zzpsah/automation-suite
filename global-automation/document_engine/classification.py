"""Deterministic document classification."""
from __future__ import annotations

KEYWORDS = {
    "order": ("आदेश", "order", "ज्ञाप", "निर्देश"),
    "circular": ("परिपत्र", "circular"),
    "letter": ("पत्र", "letter"),
    "notice": ("सूचना", "notice"),
    "memorandum": ("ज्ञापन", "memorandum", "memo"),
}


def classify(text: str, existing: str | None = None) -> dict[str, object]:
    if existing:
        return {"type": existing, "method": "ocr-taxonomy", "confidence": "MEDIUM"}
    folded = (text or "").casefold()
    hits = {kind: sum(term.casefold() in folded for term in terms) for kind, terms in KEYWORDS.items()}
    kind, count = max(hits.items(), key=lambda item: item[1])
    return {"type": kind if count else "unknown", "method": "keyword-evidence", "confidence": "MEDIUM" if count else "LOW", "evidence_count": count}
