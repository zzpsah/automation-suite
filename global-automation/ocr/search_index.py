"""Deterministic, evidence-preserving global document search."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable, Mapping, Sequence

from .document_understanding import DocumentUnderstandingGraph, UnderstandingEntity

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")

@dataclass(frozen=True)
class SearchDocument:
    document_id: str
    page_number: int
    block_id: str
    text: str

@dataclass(frozen=True)
class SearchEntity:
    document_id: str
    entity_id: str
    entity_type: str
    value: str
    page_number: int
    block_id: str
    confidence: float

@dataclass(frozen=True)
class SearchHit:
    document_id: str
    page_number: int
    block_id: str
    match_type: str
    matched_value: str
    score: float
    entity_id: str | None = None
    entity_type: str | None = None

def normalize_query(value: str) -> str:
    """Normalize only for matching; never modify source evidence."""
    return _SPACE_RE.sub(" ", value.strip()).casefold()

def _tokens(value: str) -> set[str]:
    return set(_TOKEN_RE.findall(value.casefold()))

class DocumentSearchIndex:
    """Storage-agnostic search contract with page/block provenance."""
    def __init__(self) -> None:
        self._documents: dict[str, SearchDocument] = {}
        self._entities: dict[str, SearchEntity] = {}

    def add_document(self, document: SearchDocument) -> None:
        if not document.document_id.strip() or not document.block_id.strip():
            raise ValueError("document_id and block_id must not be empty")
        self._documents[f"{document.document_id}:{document.page_number}:{document.block_id}"] = document

    def add_entity(self, document_id: str, entity: UnderstandingEntity) -> None:
        if not document_id.strip():
            raise ValueError("document_id must not be empty")
        self._entities[f"{document_id}:{entity.entity_id}"] = SearchEntity(
            document_id, entity.entity_id, entity.entity_type, entity.value,
            entity.page_number, entity.block_id, entity.confidence,
        )

    def index_understanding_graphs(self, documents: Mapping[str, DocumentUnderstandingGraph]) -> None:
        for document_id, graph in sorted(documents.items(), key=lambda item: str(item[0])):
            for entity in sorted(graph.entities, key=lambda item: (item.page_number, item.block_id, item.entity_id)):
                self.add_entity(str(document_id), entity)

    def search(self, query: str, *, limit: int = 20) -> tuple[SearchHit, ...]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        normalized = normalize_query(query)
        if not normalized:
            return ()
        query_tokens = _tokens(normalized)
        hits: list[SearchHit] = []
        for entity in self._entities.values():
            value = normalize_query(entity.value)
            if not value:
                continue
            if value == normalized:
                score, match_type = 1.0, "exact_entity"
            elif normalized in value:
                score, match_type = 0.92, "entity_contains"
            else:
                overlap = len(query_tokens & _tokens(value)) / max(len(query_tokens), 1)
                if overlap == 0:
                    continue
                score, match_type = round(0.5 + 0.4 * overlap, 6), "entity_token_overlap"
            hits.append(SearchHit(entity.document_id, entity.page_number, entity.block_id, match_type, entity.value, score, entity.entity_id, entity.entity_type))
        for document in self._documents.values():
            text = normalize_query(document.text)
            if not text:
                continue
            if text == normalized:
                score, match_type = 0.90, "exact_text"
            elif normalized in text:
                score, match_type = 0.82, "text_contains"
            else:
                overlap = len(query_tokens & _tokens(text)) / max(len(query_tokens), 1)
                if overlap == 0:
                    continue
                score, match_type = round(0.4 + 0.35 * overlap, 6), "text_token_overlap"
            hits.append(SearchHit(document.document_id, document.page_number, document.block_id, match_type, document.text, score))
        hits.sort(key=lambda h: (-h.score, h.document_id, h.page_number, h.block_id, h.match_type, h.entity_id or ""))
        return tuple(hits[:limit])

    def to_dict(self) -> dict:
        return {
            "documents": [asdict(x) for x in sorted(self._documents.values(), key=lambda x: (x.document_id, x.page_number, x.block_id))],
            "entities": [asdict(x) for x in sorted(self._entities.values(), key=lambda x: (x.document_id, x.page_number, x.block_id, x.entity_id))],
        }

def build_search_index(documents: Mapping[str, DocumentUnderstandingGraph], blocks: Mapping[str, Sequence[SearchDocument]] | None = None) -> DocumentSearchIndex:
    index = DocumentSearchIndex()
    index.index_understanding_graphs(documents)
    for _, items in sorted((blocks or {}).items(), key=lambda item: str(item[0])):
        for item in items:
            index.add_document(item)
    return index

def search_to_dict(hits: Iterable[SearchHit]) -> list[dict]:
    return [asdict(hit) for hit in hits]
