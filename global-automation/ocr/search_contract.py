"""Storage-neutral contract for persistent global OCR search adapters."""
from __future__ import annotations

from typing import Protocol, Iterable

from .search_index import SearchDocument, SearchEntity, SearchHit
from .search_filters import SearchFilter


class SearchStore(Protocol):
    """Minimal contract consumers can use without knowing the database."""

    def upsert_document(self, document: SearchDocument) -> None: ...
    def upsert_entity(self, entity: SearchEntity) -> None: ...
    def upsert_many(self, documents: Iterable[SearchDocument] = (), entities: Iterable[SearchEntity] = ()) -> None: ...
    def search(self, query: str, *, limit: int = 20, search_filter: SearchFilter | None = None) -> tuple[SearchHit, ...]: ...
    def close(self) -> None: ...


def search_with_filter(store: SearchStore, query: str, *, limit: int = 20, search_filter: SearchFilter | None = None) -> tuple[SearchHit, ...]:
    """Use the common contract and apply a filter without mutating evidence."""
    hits = store.search(query, limit=limit)
    if search_filter is None:
        return hits
    from .search_filters import filter_hits
    return filter_hits(hits, search_filter)


__all__ = ["SearchStore", "search_with_filter"]
