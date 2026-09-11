"""Deterministic field-level confidence for government-document metadata.

This module scores extracted values without rewriting source text or making
publication decisions. It is intentionally project-agnostic so consumers can
route only doubtful fields to review.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

REVIEW_THRESHOLD = 0.60


@dataclass(frozen=True)
class FieldConfidence:
    field: str
    value: str | None
    score: float
    level: str
    evidence: bool
    needs_review: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _level(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    if score >= REVIEW_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def _evidence(value: str | None, text: str) -> bool:
    if not value or not text:
        return False
    return value.casefold() in text.casefold()


def _structure_score(field: str, value: str | None) -> float:
    if not value:
        return 0.0
    value = value.strip()
    if not value:
        return 0.0
    if field == "subject":
        return 1.0 if 8 <= len(value) <= 1200 else 0.45
    if field == "authority":
        return 1.0 if 3 <= len(value) <= 300 else 0.45
    if field in {"reference_number", "order_number"}:
        if not 1 <= len(value) <= 250:
            return 0.35
        return 1.0 if re.search(r"[\w\u0900-\u097F]", value, re.UNICODE) else 0.50
    if field == "issue_date":
        return 1.0 if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else 0.35
    return 1.0 if len(value) <= 1000 else 0.45


def score_field(
    field: str,
    value: str | None,
    text: str,
    *,
    ocr_confidence: float | None = None,
    evidence_required: bool = True,
) -> FieldConfidence:
    """Score one extracted field using structure, source evidence and OCR confidence."""
    structure = _structure_score(field, value)
    evidence = _evidence(value, text)
    evidence_score = 1.0 if evidence else 0.0

    # Missing source evidence is a strong review signal, while absent OCR
    # confidence is neutral: the engine must never invent a confidence value.
    score = 0.65 * structure + (0.35 * evidence_score if evidence_required else 0.0)
    if not evidence_required:
        score = structure
    if ocr_confidence is not None:
        bounded = max(0.0, min(1.0, float(ocr_confidence)))
        score = 0.75 * score + 0.25 * bounded

    score = round(max(0.0, min(1.0, score)), 2)
    return FieldConfidence(
        field=field,
        value=value,
        score=score,
        level=_level(score),
        evidence=evidence,
        needs_review=score < REVIEW_THRESHOLD,
    )


def score_fields(
    metadata: dict[str, Any],
    text: str,
    *,
    ocr_confidence: float | None = None,
    fields: tuple[str, ...] = ("subject", "authority", "reference_number", "issue_date"),
) -> dict[str, Any]:
    """Return field-level confidence and a minimal review queue."""
    results = {
        field: score_field(
            field,
            metadata.get(field),
            text,
            ocr_confidence=ocr_confidence,
        ).to_dict()
        for field in fields
    }
    review_fields = [name for name, item in results.items() if item["needs_review"]]
    return {
        "threshold": REVIEW_THRESHOLD,
        "fields": results,
        "review": {
            "required": bool(review_fields),
            "fields": review_fields,
            "reason": "low_field_confidence" if review_fields else None,
        },
    }
