"""Layout-preserving OCR text reconstruction.

Reconstruction uses OCR span geometry to produce readable text while retaining
columns, rows, paragraph breaks, and table-like alignment. It never invents
content and does not modify the original OCR evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .region_alignment import OCRSpan


@dataclass(frozen=True)
class ReconstructionLine:
    text: str
    spans: tuple[OCRSpan, ...]
    y: float


def _line_threshold(spans: list[OCRSpan]) -> float:
    heights = [max(1.0, s.height) for s in spans]
    return max(3.0, median(heights) * 0.65)


def group_lines(spans: list[OCRSpan]) -> list[ReconstructionLine]:
    """Group spans into visual lines using vertical center proximity."""
    ordered = sorted(spans, key=lambda s: ((s.y + s.height / 2), s.x, s.text))
    lines: list[list[OCRSpan]] = []
    centers: list[float] = []
    threshold = _line_threshold(ordered) if ordered else 3.0
    for span in ordered:
        center = span.y + span.height / 2
        best = None
        best_distance = None
        for idx, line_center in enumerate(centers):
            distance = abs(center - line_center)
            if distance <= threshold and (best_distance is None or distance < best_distance):
                best, best_distance = idx, distance
        if best is None:
            lines.append([span])
            centers.append(center)
        else:
            lines[best].append(span)
            centers[best] = sum(s.y + s.height / 2 for s in lines[best]) / len(lines[best])
    result: list[ReconstructionLine] = []
    for spans_on_line, center in zip(lines, centers):
        ordered_line = tuple(sorted(spans_on_line, key=lambda s: (s.x, s.text)))
        result.append(ReconstructionLine(text=_join_spans(ordered_line), spans=ordered_line, y=center))
    return sorted(result, key=lambda line: line.y)


def _join_spans(spans: tuple[OCRSpan, ...]) -> str:
    if not spans:
        return ""
    parts: list[str] = []
    previous = None
    for span in spans:
        text = span.text.strip()
        if not text:
            continue
        if previous is None:
            parts.append(text)
        else:
            gap = span.x - previous.right
            scale = max(1.0, min(previous.height, span.height))
            parts.append(("    " if gap >= scale * 2.5 else " ") + text)
        previous = span
    return "".join(parts).strip()


def reconstruct_text(spans: list[OCRSpan], *, paragraph_gap_factor: float = 1.8) -> str:
    """Return layout-aware text with paragraph/column whitespace preserved."""
    if not spans:
        return ""
    if paragraph_gap_factor <= 0:
        raise ValueError("paragraph_gap_factor must be positive")
    lines = group_lines(spans)
    if not lines:
        return ""
    heights = [max(1.0, s.height) for line in lines for s in line.spans]
    typical_height = median(heights)
    output: list[str] = []
    previous_bottom = None
    for line in lines:
        top = min(s.y for s in line.spans)
        if previous_bottom is not None and top - previous_bottom > typical_height * paragraph_gap_factor:
            output.append("")
        output.append(line.text)
        previous_bottom = max(s.bottom for s in line.spans)
    return "\n".join(output).strip()


__all__ = ["ReconstructionLine", "group_lines", "reconstruct_text"]
