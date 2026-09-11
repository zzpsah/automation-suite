"""Project-agnostic intelligence for reconstructing document structure.

The engine works from OCR spans and geometry. It produces structural hints
without changing source OCR text and without claiming semantic truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .region_alignment import OCRSpan
from .text_reconstruction import ReconstructionLine, group_lines


@dataclass(frozen=True)
class LayoutBlock:
    block_type: str
    text: str
    lines: tuple[ReconstructionLine, ...]
    confidence: float


@dataclass(frozen=True)
class TableCell:
    row: int
    column: int
    text: str
    x: float
    y: float
    width: float
    height: float


def _overlap(a: OCRSpan, b: OCRSpan) -> float:
    left, right = max(a.x, b.x), min(a.right, b.right)
    return max(0.0, right - left)


def detect_columns(lines: list[ReconstructionLine], *, min_gap_factor: float = 3.0) -> list[list[ReconstructionLine]]:
    """Detect visually separated columns from line span gaps."""
    if not lines:
        return []
    heights = [max(1.0, s.height) for line in lines for s in line.spans]
    gap_limit = median(heights) * min_gap_factor if heights else 20.0
    columns: list[list[ReconstructionLine]] = []
    for line in lines:
        if not line.spans:
            continue
        left = min(s.x for s in line.spans)
        placed = False
        for column in columns:
            anchor = min(s.x for l in column for s in l.spans)
            if abs(left - anchor) <= gap_limit:
                column.append(line)
                placed = True
                break
        if not placed:
            columns.append([line])
    return sorted(columns, key=lambda col: min(s.x for l in col for s in l.spans))


def infer_block_type(lines: list[ReconstructionLine], *, page_height: float | None = None) -> str:
    """Infer a conservative structural block label from geometry only."""
    if not lines:
        return "empty"
    all_spans = [s for line in lines for s in line.spans]
    top = min(s.y for s in all_spans)
    bottom = max(s.bottom for s in all_spans)
    text = " ".join(line.text for line in lines).strip()
    if page_height:
        if top <= page_height * 0.12:
            return "header"
        if bottom >= page_height * 0.90:
            return "footer"
    if len(lines) <= 2 and len(text) <= 180:
        return "heading_or_label"
    return "body"


def detect_table(lines: list[ReconstructionLine]) -> list[TableCell]:
    """Convert strongly column-aligned line spans into table-like cells.

    This is intentionally conservative: a table is represented only when each
    row has multiple spans with stable x positions. It does not invent missing
    cells or values.
    """
    if len(lines) < 2:
        return []
    row_spans = [list(line.spans) for line in lines if len(line.spans) >= 2]
    if len(row_spans) < 2:
        return []
    anchors = sorted(s.x for s in row_spans[0])
    if len(anchors) < 2:
        return []
    cells: list[TableCell] = []
    for row_index, spans in enumerate(row_spans, 1):
        ordered = sorted(spans, key=lambda s: s.x)
        if len(ordered) != len(anchors):
            return []
        tolerance = max(4.0, median(max(1.0, s.width) for s in ordered) * 0.8)
        if any(abs(a - s.x) > tolerance for a, s in zip(anchors, ordered)):
            return []
        for col_index, span in enumerate(ordered, 1):
            cells.append(TableCell(row_index, col_index, span.text.strip(), span.x, span.y, span.width, span.height))
    return cells


def analyze_layout(spans: Iterable[OCRSpan], *, page_height: float | None = None) -> dict:
    """Return deterministic layout intelligence suitable for downstream APIs."""
    span_list = list(spans)
    lines = group_lines(span_list)
    columns = detect_columns(lines)
    tables = detect_table(lines)
    blocks: list[LayoutBlock] = []
    if lines:
        blocks.append(LayoutBlock(
            infer_block_type(lines, page_height=page_height),
            "\n".join(line.text for line in lines),
            tuple(lines),
            0.5 if tables else 0.4,
        ))
    return {
        "span_count": len(span_list),
        "line_count": len(lines),
        "column_count": len(columns),
        "table_detected": bool(tables),
        "table_cells": [cell.__dict__ for cell in tables],
        "blocks": [
            {"type": block.block_type, "text": block.text, "confidence": block.confidence}
            for block in blocks
        ],
    }


__all__ = ["LayoutBlock", "TableCell", "detect_columns", "detect_table", "infer_block_type", "analyze_layout"]
