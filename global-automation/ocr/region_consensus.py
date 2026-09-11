"""Region-level OCR disagreement diagnostics using backend bounding boxes."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .backend import OCRResult
from .region_alignment import OCRSpan, align_regions


@dataclass(frozen=True)
class RegionDisagreement:
    backend_a: str
    backend_b: str
    text_a: str
    text_b: str
    geometry_score: float
    text_similarity: float
    disagreement: bool


def compare_regions(results: list[OCRResult]) -> list[RegionDisagreement]:
    """Compare geometrically aligned OCR regions while preserving all outputs.

    If no backend exposes spans, returns an empty list rather than guessing
    geometry from text positions.
    """
    spans: list[OCRSpan] = []
    for result in results:
        spans.extend(result.spans)
    if len({span.backend for span in spans}) < 2:
        return []

    diagnostics: list[RegionDisagreement] = []
    for left, right, geometry_score in align_regions(spans):
        similarity = SequenceMatcher(None, left.text, right.text).ratio()
        diagnostics.append(RegionDisagreement(
            backend_a=left.backend,
            backend_b=right.backend,
            text_a=left.text,
            text_b=right.text,
            geometry_score=geometry_score,
            text_similarity=round(similarity, 4),
            disagreement=left.text.strip() != right.text.strip(),
        ))
    return diagnostics


__all__ = ["RegionDisagreement", "compare_regions"]
