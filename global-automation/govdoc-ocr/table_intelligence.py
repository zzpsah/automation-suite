"""Evidence-only table structure helpers derived from OCR geometry."""
from __future__ import annotations
from .layout import group_lines
from .regions import OCRRegion, regions_to_dict


def infer_columns(regions: list[OCRRegion | dict], *, y_tolerance: int = 12, min_rows: int = 2) -> list[dict]:
    """Find repeated x-aligned cells across lines without declaring a table."""
    lines = group_lines(regions, y_tolerance=y_tolerance)
    if len(lines) < min_rows:
        return []
    anchors: list[int] = []
    for line in lines:
        for r in line:
            x = r["bbox"][0]
            if not any(abs(x-a) <= 12 for a in anchors):
                anchors.append(x)
    anchors.sort()
    repeated = [x for x in anchors if sum(any(abs(r["bbox"][0]-x) <= 12 for r in line) for line in lines) >= min_rows]
    return [{"column_index": i, "x": x, "support_rows": sum(any(abs(r["bbox"][0]-x) <= 12 for r in line) for line in lines)} for i, x in enumerate(repeated)]


def table_evidence(regions: list[OCRRegion | dict], *, y_tolerance: int = 12, min_rows: int = 2) -> dict:
    normalized = regions_to_dict(regions)
    lines = group_lines(normalized, y_tolerance=y_tolerance)
    columns = infer_columns(normalized, y_tolerance=y_tolerance, min_rows=min_rows)
    return {
        "region_count": len(normalized),
        "row_count": len(lines),
        "candidate_columns": columns,
        "signals": {
            "repeated_columns": len(columns) >= 2,
            "multiple_rows": len(lines) >= min_rows,
            "table_candidate": len(columns) >= 2 and len(lines) >= min_rows,
        },
        "evidence_only": True,
    }
