"""Conservative reading-order reconstruction from OCR geometry.

The output is evidence-derived only: no text is invented, merged or corrected.
"""
from __future__ import annotations
from .layout import rows
from .regions import OCRRegion


def reading_lines(regions: list[OCRRegion | dict], *, y_tolerance: int = 12) -> list[list[dict]]:
    """Group OCR regions into visual lines and sort each line left-to-right."""
    return rows(regions, y_tolerance=y_tolerance)


def reading_order(regions: list[OCRRegion | dict], *, y_tolerance: int = 12) -> list[dict]:
    """Return regions in deterministic line-first reading order."""
    ordered: list[dict] = []
    for line in reading_lines(regions, y_tolerance=y_tolerance):
        ordered.extend(line)
    return ordered


def line_text(regions: list[OCRRegion | dict], *, y_tolerance: int = 12) -> list[str]:
    """Build line strings from existing OCR text, preserving region order."""
    return [" ".join(r["text"] for r in line if r.get("text")) for line in reading_lines(regions, y_tolerance=y_tolerance)]
