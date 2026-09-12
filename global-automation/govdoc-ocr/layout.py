"""Deterministic layout helpers for OCR regions and simple government forms.

P42 adds geometry-aware line/column analysis while keeping the original
helpers backward compatible.  All outputs are evidence/signals only; this
module must never fabricate geometry or assert semantic structure.
"""
from __future__ import annotations

from .regions import OCRRegion, regions_to_dict


def _center_y(region: dict) -> float:
    return (region["bbox"][1] + region["bbox"][3]) / 2


def _vertical_overlap(a: dict, b: dict) -> float:
    top = max(a["bbox"][1], b["bbox"][1])
    bottom = min(a["bbox"][3], b["bbox"][3])
    overlap = max(0, bottom - top)
    ah = max(1, a["bbox"][3] - a["bbox"][1])
    bh = max(1, b["bbox"][3] - b["bbox"][1])
    return overlap / min(ah, bh)


def _horizontal_gap(a: dict, b: dict) -> int:
    if a["bbox"][2] <= b["bbox"][0]:
        return b["bbox"][0] - a["bbox"][2]
    if b["bbox"][2] <= a["bbox"][0]:
        return a["bbox"][0] - b["bbox"][2]
    return 0


def order_reading(regions: list[OCRRegion | dict]) -> list[dict]:
    """Return deterministic reading order, respecting likely columns.

    Regions are first grouped into visual lines using vertical overlap/centre
    distance. Lines are then assigned to columns when their x-ranges indicate
    a stable left/right separation. Ambiguous layouts fall back to the legacy
    top-to-bottom/left-to-right ordering.
    """
    normalized = regions_to_dict(regions)
    if len(normalized) < 2:
        return normalized
    lines = group_lines(normalized)
    if len(lines) < 2:
        return sorted(normalized, key=lambda r: (r["bbox"][1], r["bbox"][0], r["id"]))
    columns = detect_columns(normalized)
    if len(columns) < 2:
        return [region for line in lines for region in line]
    column_ids = {region["id"]: index for index, column in enumerate(columns) for region in column}
    # A column is read top-to-bottom before moving to the next column. This is
    # only used where a genuine horizontal separation signal exists.
    return sorted(
        normalized,
        key=lambda r: (column_ids.get(r["id"], 0), r["bbox"][1], r["bbox"][0], r["id"]),
    )


def group_lines(regions: list[OCRRegion | dict], y_tolerance: int = 12) -> list[list[dict]]:
    """Cluster regions into visual lines using geometry, not text content."""
    normalized = regions_to_dict(regions)
    result: list[list[dict]] = []
    for region in sorted(normalized, key=lambda r: (_center_y(r), r["bbox"][0], r["id"])):
        target = None
        best_distance = None
        for line in result:
            anchor = line[0]
            distance = abs(_center_y(anchor) - _center_y(region))
            if (distance <= y_tolerance or _vertical_overlap(anchor, region) >= 0.5) and (
                best_distance is None or distance < best_distance
            ):
                target, best_distance = line, distance
        if target is None:
            result.append([region])
        else:
            target.append(region)
            target.sort(key=lambda r: (r["bbox"][0], r["id"]))
    result.sort(key=lambda line: (_center_y(line[0]), line[0]["bbox"][0], line[0]["id"]))
    return result


def detect_columns(
    regions: list[OCRRegion | dict],
    min_column_regions: int = 2,
    min_gap: int = 24,
) -> list[list[dict]]:
    """Return likely visual columns as evidence, or one column if ambiguous."""
    normalized = regions_to_dict(regions)
    if len(normalized) < min_column_regions * 2:
        return [sorted(normalized, key=lambda r: (r["bbox"][1], r["bbox"][0], r["id"]))]

    candidates = sorted(normalized, key=lambda r: (r["bbox"][0], r["bbox"][2], r["id"]))
    clusters: list[list[dict]] = []
    for region in candidates:
        if not clusters:
            clusters.append([region])
            continue
        current = clusters[-1]
        right = max(r["bbox"][2] for r in current)
        left = region["bbox"][0]
        if left - right >= min_gap:
            clusters.append([region])
        else:
            current.append(region)

    clusters = [c for c in clusters if len(c) >= min_column_regions]
    if len(clusters) < 2:
        return [sorted(normalized, key=lambda r: (r["bbox"][1], r["bbox"][0], r["id"]))]
    return sorted(clusters, key=lambda c: (min(r["bbox"][0] for r in c), c[0]["id"]))


def rows(regions: list[OCRRegion | dict], y_tolerance: int = 12) -> list[list[dict]]:
    """Backward-compatible alias for geometry-aware line grouping."""
    return group_lines(regions, y_tolerance=y_tolerance)


def table_candidates(regions: list[OCRRegion | dict], y_tolerance: int = 12, min_columns: int = 2) -> list[list[dict]]:
    """Return evidence rows only; never assert that a table exists."""
    return [row for row in rows(regions, y_tolerance) if len(row) >= min_columns]


def layout_summary(
    regions: list[OCRRegion | dict],
    *,
    page_width: int | None = None,
    page_height: int | None = None,
) -> dict:
    """Build a compact, deterministic layout evidence object."""
    normalized = regions_to_dict(regions)
    columns = detect_columns(normalized)
    lines = group_lines(normalized)
    ordered = order_reading(normalized)
    return {
        "region_count": len(normalized),
        "line_count": len(lines),
        "column_count": len(columns),
        "columns": [[r["id"] for r in column] for column in columns] if normalized else [],
        "reading_order": [r["id"] for r in ordered],
        "page_width": page_width,
        "page_height": page_height,
        "signals": {
            "multi_column": len(columns) > 1,
            "geometry_based": bool(normalized),
        },
    }
