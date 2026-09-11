"""Evidence-preserving document structure intelligence.

Turns OCR spans into explicit blocks, columns, tables, headers, footers and
sections. All decisions are heuristic and carry confidence; no content is
invented and source OCR remains untouched.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import median
from typing import Iterable

from .layout_intelligence import detect_columns, detect_table, infer_block_type
from .region_alignment import OCRSpan
from .text_reconstruction import ReconstructionLine, group_lines


@dataclass(frozen=True)
class StructureBlock:
    block_id: str
    block_type: str
    text: str
    page_number: int
    confidence: float
    column: int | None = None


@dataclass(frozen=True)
class DocumentStructure:
    pages: tuple[dict, ...]
    blocks: tuple[StructureBlock, ...]
    reading_order: tuple[str, ...]
    table_count: int


def _block_confidence(block_type: str, lines: list[ReconstructionLine]) -> float:
    if not lines:
        return 0.0
    geometry = min(1.0, len(lines) / 3.0)
    return round(min(0.95, 0.35 + geometry * 0.30 + (0.15 if block_type in {"header", "footer"} else 0.0)), 2)


def build_page_structure(page_number: int, spans: Iterable[OCRSpan], *, page_height: float | None = None) -> tuple[list[StructureBlock], dict]:
    span_list = list(spans)
    lines = group_lines(span_list)
    columns = detect_columns(lines)
    tables = detect_table(lines)
    blocks: list[StructureBlock] = []
    for index, line_group in enumerate(columns or ([lines] if lines else []), 1):
        if not line_group:
            continue
        block_type = infer_block_type(line_group, page_height=page_height)
        block_id = f"p{page_number}-b{index}"
        blocks.append(StructureBlock(
            block_id,
            "table" if tables and len(columns) > 1 else block_type,
            "\n".join(line.text for line in sorted(line_group, key=lambda l: l.y)),
            page_number,
            _block_confidence(block_type, line_group),
            index if len(columns) > 1 else None,
        ))
    return blocks, {
        "page_number": page_number,
        "line_count": len(lines),
        "column_count": len(columns),
        "table_detected": bool(tables),
    }


def build_document_structure(page_spans: dict[int, Iterable[OCRSpan]], *, page_heights: dict[int, float] | None = None) -> DocumentStructure:
    """Build deterministic page/block structure from geometry-aware OCR."""
    all_blocks: list[StructureBlock] = []
    page_info: list[dict] = []
    table_count = 0
    for page_number in sorted(page_spans):
        blocks, info = build_page_structure(page_number, page_spans[page_number], page_height=(page_heights or {}).get(page_number))
        all_blocks.extend(blocks)
        page_info.append(info)
        table_count += int(info["table_detected"])
    ordered = tuple(block.block_id for block in sorted(all_blocks, key=lambda b: (b.page_number, b.column or 0, b.block_id)))
    return DocumentStructure(tuple(page_info), tuple(all_blocks), ordered, table_count)


def structure_to_dict(structure: DocumentStructure) -> dict:
    return {
        "pages": list(structure.pages),
        "blocks": [asdict(block) for block in structure.blocks],
        "reading_order": list(structure.reading_order),
        "table_count": structure.table_count,
    }


__all__ = ["StructureBlock", "DocumentStructure", "build_page_structure", "build_document_structure", "structure_to_dict"]
