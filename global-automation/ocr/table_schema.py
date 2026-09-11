"""Evidence-preserving table schema built from detected OCR cells."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .layout_intelligence import TableCell


@dataclass(frozen=True)
class StructuredTableCell:
    row: int
    column: int
    text: str
    x: float
    y: float
    width: float
    height: float
    row_span: int = 1
    column_span: int = 1


@dataclass(frozen=True)
class StructuredTable:
    table_id: str
    cells: tuple[StructuredTableCell, ...]
    row_count: int
    column_count: int
    confidence: float


def build_table(cells: Iterable[TableCell], *, table_id: str = "table-1", confidence: float = 0.7) -> StructuredTable:
    """Normalize detected cells into an explicit schema; never invent cells."""
    source = tuple(cells)
    if not source:
        raise ValueError("cells must not be empty")
    if not table_id.strip():
        raise ValueError("table_id must not be empty")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    normalized = tuple(
        StructuredTableCell(c.row, c.column, c.text, c.x, c.y, c.width, c.height)
        for c in sorted(source, key=lambda c: (c.row, c.column, c.y, c.x))
    )
    return StructuredTable(table_id, normalized, max(c.row for c in normalized), max(c.column for c in normalized), round(confidence, 2))


def table_to_dict(table: StructuredTable) -> dict:
    return {
        "table_id": table.table_id,
        "cells": [asdict(cell) for cell in table.cells],
        "row_count": table.row_count,
        "column_count": table.column_count,
        "confidence": table.confidence,
    }


__all__ = ["StructuredTableCell", "StructuredTable", "build_table", "table_to_dict"]
