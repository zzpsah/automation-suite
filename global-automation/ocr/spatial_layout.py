"""Deterministic spatial layout primitives for government documents.

This layer classifies OCR spans by geometry only. It never changes source text
and deliberately avoids pretending that geometry alone proves semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .region_alignment import OCRSpan


@dataclass(frozen=True)
class LayoutRegion:
    label: str
    spans: tuple[OCRSpan, ...]
    confidence: float


def _center(span: OCRSpan) -> tuple[float, float]:
    return span.x + span.width / 2.0, span.y + span.height / 2.0


def classify_layout(spans: Iterable[OCRSpan], *, page_width: int, page_height: int) -> tuple[LayoutRegion, ...]:
    """Assign conservative geometric regions to OCR spans.

    Labels are spatial hints, not semantic extraction results.
    """
    if page_width <= 0 or page_height <= 0:
        raise ValueError("page dimensions must be positive")
    items = tuple(spans)
    buckets: dict[str, list[OCRSpan]] = {"header": [], "body": [], "footer": [], "margin": []}
    for span in items:
        cx, cy = _center(span)
        if cx < 0 or cy < 0 or cx > page_width or cy > page_height:
            buckets["margin"].append(span)
        elif cy <= page_height * 0.15:
            buckets["header"].append(span)
        elif cy >= page_height * 0.88:
            buckets["footer"].append(span)
        elif cx <= page_width * 0.08 or cx >= page_width * 0.92:
            buckets["margin"].append(span)
        else:
            buckets["body"].append(span)
    regions: list[LayoutRegion] = []
    for label, values in buckets.items():
        if values:
            regions.append(LayoutRegion(label, tuple(values), 1.0))
    return tuple(regions)


__all__ = ["LayoutRegion", "classify_layout"]
