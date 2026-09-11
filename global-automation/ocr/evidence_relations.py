"""Conservative extraction of explicitly stated document relationships."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable

from .document_structure import StructureBlock


@dataclass(frozen=True)
class EvidenceRelation:
    relation_type: str
    source_block_id: str
    target_reference: str
    confidence: float
    evidence_text: str


_PATTERNS = (
    ("continuation_of", re.compile(r"(?:in\s+)?continuation\s+of\s*[:#-]?\s*([A-Za-z0-9./_-]{3,})", re.I), 0.96),
    ("supersedes", re.compile(r"supersedes?\s*[:#-]?\s*([A-Za-z0-9./_-]{3,})", re.I), 0.97),
    ("replaces", re.compile(r"replaces?\s*[:#-]?\s*([A-Za-z0-9./_-]{3,})", re.I), 0.95),
    ("के_क्रम_में", re.compile(r"(?:के\s+क्रम\s+में|के\s+अनुसरण\s+में)\s*[:#-]?\s*([A-Za-z0-9./_-]{3,})", re.I), 0.94),
)


def extract_evidence_relations(blocks: Iterable[StructureBlock]) -> tuple[EvidenceRelation, ...]:
    """Return only relationships whose marker and target are explicitly present."""
    result: list[EvidenceRelation] = []
    for block in sorted(blocks, key=lambda b: (b.page_number, b.y, b.x, b.block_id)):
        for relation_type, pattern, confidence in _PATTERNS:
            for match in pattern.finditer(block.text):
                result.append(EvidenceRelation(relation_type, block.block_id, match.group(1), confidence, match.group(0)))
    result.sort(key=lambda r: (r.source_block_id, r.relation_type, r.target_reference))
    return tuple(result)


def evidence_relations_to_dict(relations: Iterable[EvidenceRelation]) -> dict:
    return {"relations": [asdict(item) for item in relations]}


__all__ = ["EvidenceRelation", "extract_evidence_relations", "evidence_relations_to_dict"]
