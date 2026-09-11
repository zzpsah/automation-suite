"""Evidence-preserving global reading-order optimization.

The optimizer orders already detected structure blocks using page position,
column bands, and structural roles. It never changes block text or source OCR.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ReadingOrderBlock:
    """Minimal geometry needed to optimize an existing structure block."""

    block_id: str
    page_number: int
    block_type: str
    x: float
    y: float
    width: float
    height: float
    column: int | None = None

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


def _vertical_overlap(a: ReadingOrderBlock, b: ReadingOrderBlock) -> float:
    return max(0.0, min(a.bottom, b.bottom) - max(a.y, b.y))


def _overlap_ratio(a: ReadingOrderBlock, b: ReadingOrderBlock) -> float:
    overlap = _vertical_overlap(a, b)
    if overlap <= 0:
        return 0.0
    return overlap / max(1.0, min(a.height, b.height))


def optimize_reading_order(
    blocks: Iterable[ReadingOrderBlock],
    *,
    column_overlap_threshold: float = 0.35,
) -> tuple[str, ...]:
    """Return deterministic human-style reading order for mixed-layout blocks.

    Headers are read before body content and footers after body content on each
    page. Body blocks are grouped into visually overlapping columns, then read
    top-to-bottom within each column and left-to-right across column bands.
    Explicit column numbers are preferred when supplied.
    """
    if not 0.0 <= column_overlap_threshold <= 1.0:
        raise ValueError("column_overlap_threshold must be between 0 and 1")

    page_blocks: dict[int, list[ReadingOrderBlock]] = {}
    for block in blocks:
        page_blocks.setdefault(block.page_number, []).append(block)

    ordered: list[str] = []
    for page_number in sorted(page_blocks):
        page = page_blocks[page_number]
        headers = sorted((b for b in page if b.block_type == "header"), key=lambda b: (b.y, b.x, b.block_id))
        footers = sorted((b for b in page if b.block_type == "footer"), key=lambda b: (b.y, b.x, b.block_id))
        body = [b for b in page if b.block_type not in {"header", "footer"}]

        ordered.extend(b.block_id for b in headers)

        # Explicit columns are authoritative when present.
        if any(b.column is not None for b in body):
            columns: dict[int, list[ReadingOrderBlock]] = {}
            unassigned: list[ReadingOrderBlock] = []
            for block in body:
                if block.column is None:
                    unassigned.append(block)
                else:
                    columns.setdefault(block.column, []).append(block)
            for column in sorted(columns):
                ordered.extend(b.block_id for b in sorted(columns[column], key=lambda b: (b.y, b.x, b.block_id)))
            ordered.extend(b.block_id for b in sorted(unassigned, key=lambda b: (b.y, b.x, b.block_id)))
        else:
            # Infer column bands from horizontal overlap with a stable left edge.
            bands: list[list[ReadingOrderBlock]] = []
            for block in sorted(body, key=lambda b: (b.x, b.y, b.block_id)):
                placed = False
                for band in bands:
                    representative = min(band, key=lambda b: (b.y, b.block_id))
                    horizontal_overlap = max(0.0, min(block.right, representative.right) - max(block.x, representative.x))
                    ratio = horizontal_overlap / max(1.0, min(block.width, representative.width))
                    if ratio >= column_overlap_threshold or abs(block.x - representative.x) <= max(8.0, min(block.width, representative.width) * 0.15):
                        band.append(block)
                        placed = True
                        break
                if not placed:
                    bands.append([block])
            bands.sort(key=lambda band: (min(b.x for b in band), min(b.y for b in band), min(b.block_id for b in band)))
            for band in bands:
                ordered.extend(b.block_id for b in sorted(band, key=lambda b: (b.y, b.x, b.block_id)))

        ordered.extend(b.block_id for b in footers)

    return tuple(ordered)


__all__ = ["ReadingOrderBlock", "optimize_reading_order"]
