"""Conservative handwriting-review adapter contract.

This module detects *review candidates* from OCR evidence. It does not perform
handwriting recognition or infer identity/signature validity. A future local
vision backend can implement the optional recognizer contract without changing
consumers of the GovDOC service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class HandwritingCandidate:
    region_id: str | None
    bbox: list[float] | None
    reason: str
    confidence: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "bbox": self.bbox,
            "reason": self.reason,
            "confidence": self.confidence,
            "requires_review": True,
        }


class HandwritingRecognizer(Protocol):
    name: str

    def recognize(self, image_path: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]: ...


def candidates_from_regions(
    regions: list[dict[str, Any]], *, confidence_threshold: float = 0.65
) -> list[HandwritingCandidate]:
    """Return low-confidence regions as conservative handwriting-review candidates."""
    output: list[HandwritingCandidate] = []
    for region in regions:
        confidence = region.get("confidence")
        if confidence is None:
            continue
        try:
            score = float(confidence)
        except (TypeError, ValueError):
            continue
        if score < confidence_threshold:
            bbox = region.get("bbox")
            output.append(
                HandwritingCandidate(
                    region_id=region.get("id"),
                    bbox=list(bbox) if isinstance(bbox, (list, tuple)) else None,
                    reason="low-ocr-confidence-review",
                    confidence=score,
                )
            )
    return output


def review_contract(regions: list[dict[str, Any]], *, confidence_threshold: float = 0.65) -> dict[str, Any]:
    candidates = candidates_from_regions(regions, confidence_threshold=confidence_threshold)
    return {
        "supported": True,
        "recognition_available": False,
        "candidate_count": len(candidates),
        "candidates": [candidate.to_dict() for candidate in candidates],
        "evidence_only": True,
        "interpretation": "Review candidates only; no handwriting recognition or identity/authenticity claim.",
    }
