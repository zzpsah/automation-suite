"""Deterministic, evidence-preserving filters for global OCR search results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .search_index import SearchHit


@dataclass(frozen=True)
class SearchFilter:
    document_ids: frozenset[str] = frozenset()
    page_numbers: frozenset[int] = frozenset()
    block_ids: frozenset[str] = frozenset()
    entity_types: frozenset[str] = frozenset()
    min_score: float | None = None

    def __post_init__(self) -> None:
        if self.min_score is not None and not 0.0 <= self.min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")


def filter_hits(hits: Iterable[SearchHit], search_filter: SearchFilter) -> tuple[SearchHit, ...]:
    """Filter existing search hits without changing their evidence or ranking."""
    result = []
    for hit in hits:
        if search_filter.document_ids and hit.document_id not in search_filter.document_ids:
            continue
        if search_filter.page_numbers and hit.page_number not in search_filter.page_numbers:
            continue
        if search_filter.block_ids and hit.block_id not in search_filter.block_ids:
            continue
        if search_filter.entity_types and hit.entity_type not in search_filter.entity_types:
            continue
        if search_filter.min_score is not None and hit.score < search_filter.min_score:
            continue
        result.append(hit)
    return tuple(result)


def filter_to_dict(search_filter: SearchFilter) -> dict:
    return {
        "document_ids": sorted(search_filter.document_ids),
        "page_numbers": sorted(search_filter.page_numbers),
        "block_ids": sorted(search_filter.block_ids),
        "entity_types": sorted(search_filter.entity_types),
        "min_score": search_filter.min_score,
    }


__all__ = ["SearchFilter", "filter_hits", "filter_to_dict"]
