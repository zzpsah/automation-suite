"""Deterministic layout helpers for OCR regions and simple government forms."""
from __future__ import annotations
from .regions import OCRRegion, regions_to_dict

def order_reading(regions: list[OCRRegion | dict]) -> list[dict]:
    normalized = regions_to_dict(regions)
    return sorted(normalized, key=lambda r: (r["bbox"][1], r["bbox"][0], r["id"]))

def rows(regions: list[OCRRegion | dict], y_tolerance: int = 12) -> list[list[dict]]:
    ordered = order_reading(regions); result: list[list[dict]] = []
    for region in ordered:
        y = region["bbox"][1]
        target = next((row for row in result if abs(row[0]["bbox"][1] - y) <= y_tolerance), None)
        if target is None: result.append([region])
        else: target.append(region)
    return [sorted(row, key=lambda r: r["bbox"][0]) for row in result]

def table_candidates(regions: list[OCRRegion | dict], y_tolerance: int = 12, min_columns: int = 2) -> list[list[dict]]:
    """Return evidence rows only; never assert that a table exists."""
    return [row for row in rows(regions, y_tolerance) if len(row) >= min_columns]
