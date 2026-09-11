"""Geometry-aware OCR region alignment utilities.

The module is backend-agnostic. It aligns OCR spans by bounding-box overlap and
keeps source text untouched. Backends may opt into this richer representation
without changing the stable text-only OCR API.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class OCRSpan:
    text: str
    backend: str
    x: float
    y: float
    width: float
    height: float
    confidence: float | None = None

    @property
    def right(self) -> float:
        return self.x + max(0.0, self.width)

    @property
    def bottom(self) -> float:
        return self.y + max(0.0, self.height)


def _iou(a: OCRSpan, b: OCRSpan) -> float:
    left, top = max(a.x, b.x), max(a.y, b.y)
    right, bottom = min(a.right, b.right), min(a.bottom, b.bottom)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    area_a = max(0.0, a.width) * max(0.0, a.height)
    area_b = max(0.0, b.width) * max(0.0, b.height)
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


def _center_distance(a: OCRSpan, b: OCRSpan) -> float:
    return hypot((a.x + a.width / 2) - (b.x + b.width / 2),
                 (a.y + a.height / 2) - (b.y + b.height / 2))


def align_regions(
    spans: list[OCRSpan],
    *,
    min_iou: float = 0.20,
    max_center_distance_factor: float = 2.5,
) -> list[tuple[OCRSpan, OCRSpan, float]]:
    """Greedily align spans from different backends by geometry.

    Each span is matched at most once. IoU is preferred; nearby non-overlapping
    boxes can match when their center distance is small relative to box size.
    Returns deterministic pairs with a geometry score in [0, 1].
    """
    if not 0.0 <= min_iou <= 1.0:
        raise ValueError("min_iou must be between 0 and 1")
    if max_center_distance_factor <= 0:
        raise ValueError("max_center_distance_factor must be positive")

    ordered = sorted(spans, key=lambda s: (s.backend, s.y, s.x, s.text))
    used: set[int] = set()
    pairs: list[tuple[OCRSpan, OCRSpan, float]] = []
    for i, source in enumerate(ordered):
        if i in used:
            continue
        candidates: list[tuple[float, float, int, OCRSpan]] = []
        source_scale = max(1.0, hypot(source.width, source.height))
        for j, target in enumerate(ordered):
            if i == j or j in used or target.backend == source.backend:
                continue
            iou = _iou(source, target)
            distance = _center_distance(source, target)
            near = distance <= max(source_scale, hypot(target.width, target.height)) * max_center_distance_factor
            if iou >= min_iou or near:
                score = iou if iou >= min_iou else max(0.0, 1.0 - distance / (source_scale * max_center_distance_factor)) * 0.5
                candidates.append((score, -distance, j, target))
        if not candidates:
            continue
        _, _, j, target = max(candidates, key=lambda item: (item[0], item[1], -item[2]))
        used.add(i)
        used.add(j)
        pairs.append((source, target, round(max(0.0, min(1.0, candidates[[c[2] for c in candidates].index(j)][0])), 4)))
    return pairs


__all__ = ["OCRSpan", "align_regions"]
