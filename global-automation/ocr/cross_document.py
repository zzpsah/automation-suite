"""Evidence-preserving cross-document intelligence for OCR graphs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable, Mapping

from .document_understanding import DocumentUnderstandingGraph, UnderstandingEntity

_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class CrossDocumentRelation:
    source_document_id: str
    target_document_id: str
    relation_type: str
    confidence: float
    source_entity_id: str
    target_entity_id: str
    reason: str


@dataclass(frozen=True)
class CrossDocumentGraph:
    relations: tuple[CrossDocumentRelation, ...]


def _normalize(value: str) -> str:
    """Normalize only for exact matching; never replace source evidence."""
    return _SPACE_RE.sub(" ", value.strip()).casefold()


def _entity_key(entity: UnderstandingEntity) -> tuple[str, str]:
    return entity.entity_type, _normalize(entity.value)


def build_cross_document_graph(
    documents: Mapping[str, DocumentUnderstandingGraph],
) -> CrossDocumentGraph:
    """Relate documents only through exact normalized entity matches.

    The baseline deliberately avoids inferring legal/causal relationships such as
    supersession, same-case identity, chronology, or references from dates alone.
    """
    document_items = sorted((str(doc_id), graph) for doc_id, graph in documents.items())
    if any(not doc_id.strip() for doc_id, _ in document_items):
        raise ValueError("document IDs must not be empty")
    relations: list[CrossDocumentRelation] = []
    indexed: dict[tuple[str, str], list[tuple[str, UnderstandingEntity]]] = {}
    for doc_id, graph in document_items:
        for entity in graph.entities:
            key = _entity_key(entity)
            if not key[1]:
                continue
            indexed.setdefault(key, []).append((doc_id, entity))

    relation_by_type = {
        "reference": ("shared_reference", 0.96),
        "email": ("shared_contact", 0.94),
        "authority": ("shared_authority", 0.90),
    }
    for (entity_type, normalized), matches in sorted(indexed.items()):
        if entity_type not in relation_by_type or not normalized:
            continue
        relation_type, confidence = relation_by_type[entity_type]
        matches = sorted(matches, key=lambda item: (item[0], item[1].entity_id))
        for left_index, (left_doc, left_entity) in enumerate(matches):
            for right_doc, right_entity in matches[left_index + 1 :]:
                if left_doc == right_doc:
                    continue
                relations.append(CrossDocumentRelation(
                    source_document_id=left_doc,
                    target_document_id=right_doc,
                    relation_type=relation_type,
                    confidence=confidence,
                    source_entity_id=left_entity.entity_id,
                    target_entity_id=right_entity.entity_id,
                    reason=f"exact normalized {entity_type} match",
                ))

    relations.sort(key=lambda r: (
        r.source_document_id, r.target_document_id, r.relation_type,
        r.source_entity_id, r.target_entity_id,
    ))
    return CrossDocumentGraph(tuple(relations))


def cross_document_graph_to_dict(graph: CrossDocumentGraph) -> dict:
    return {"relations": [asdict(relation) for relation in graph.relations]}


__all__ = [
    "CrossDocumentRelation",
    "CrossDocumentGraph",
    "build_cross_document_graph",
    "cross_document_graph_to_dict",
]
