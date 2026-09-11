"""Evidence-preserving semantic understanding graph for OCR documents."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable

from .document_structure import StructureBlock
from .structure_graph import StructureGraph

_REF_RE = re.compile(r"\b(?:ref(?:erence)?|पत्रांक|ज्ञापांक|क्रमांक)\s*[:./-]?\s*([A-Za-z0-9][A-Za-z0-9./_-]{2,})", re.I)
_DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b", re.I)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


@dataclass(frozen=True)
class UnderstandingEntity:
    entity_id: str
    entity_type: str
    value: str
    page_number: int
    block_id: str
    confidence: float


@dataclass(frozen=True)
class UnderstandingRelation:
    source_id: str
    target_id: str
    relation_type: str
    confidence: float
    evidence_block_id: str
    reason: str


@dataclass(frozen=True)
class DocumentUnderstandingGraph:
    entities: tuple[UnderstandingEntity, ...]
    relations: tuple[UnderstandingRelation, ...]


def _entity(entity_type: str, value: str, block: StructureBlock, index: int, confidence: float) -> UnderstandingEntity:
    return UnderstandingEntity(f"{entity_type}:{block.block_id}:{index}", entity_type, value, block.page_number, block.block_id, round(confidence, 2))


def build_understanding_graph(
    blocks: Iterable[StructureBlock],
    structure_graph: StructureGraph | None = None,
) -> DocumentUnderstandingGraph:
    """Extract only explicitly matched entities and conservative graph relations."""
    source = tuple(sorted(blocks, key=lambda b: (b.page_number, b.y, b.x, b.block_id)))
    entities: list[UnderstandingEntity] = []
    for block in source:
        values: list[tuple[str, str, float]] = []
        values += [("reference", m.group(1), 0.88) for m in _REF_RE.finditer(block.text)]
        values += [("date", m.group(0), 0.86) for m in _DATE_RE.finditer(block.text)]
        values += [("email", m.group(0), 0.92) for m in _EMAIL_RE.finditer(block.text)]
        for index, (kind, value, confidence) in enumerate(values, 1):
            entities.append(_entity(kind, value, block, index, confidence))
        lower = block.text.casefold()
        if any(marker in lower for marker in ("district education officer", "जिला शिक्षा पदाधिकारी", "education officer")):
            entities.append(_entity("authority", block.text.strip(), block, 1, 0.72))

    relations: list[UnderstandingRelation] = []
    if structure_graph:
        entity_by_block: dict[str, list[UnderstandingEntity]] = {}
        for entity in entities:
            entity_by_block.setdefault(entity.block_id, []).append(entity)
        for edge in structure_graph.edges:
            if edge.edge_type not in {"continuation", "entity_continuity"}:
                continue
            left = entity_by_block.get(edge.source_id, ())
            right = entity_by_block.get(edge.target_id, ())
            for a in left:
                for b in right:
                    relations.append(UnderstandingRelation(a.entity_id, b.entity_id, edge.edge_type, edge.confidence, edge.target_id, edge.reason))
    entities.sort(key=lambda e: (e.page_number, e.block_id, e.entity_type, e.entity_id))
    relations.sort(key=lambda r: (r.source_id, r.target_id, r.relation_type))
    return DocumentUnderstandingGraph(tuple(entities), tuple(relations))


def understanding_graph_to_dict(graph: DocumentUnderstandingGraph) -> dict:
    return {"entities": [asdict(e) for e in graph.entities], "relations": [asdict(r) for r in graph.relations]}


__all__ = ["UnderstandingEntity", "UnderstandingRelation", "DocumentUnderstandingGraph", "build_understanding_graph", "understanding_graph_to_dict"]
