"""Optional Supabase/Postgres persistence adapter for global OCR search.

The adapter is deliberately isolated from OCR core. It requires the optional
``supabase`` Python package and an already-created client; credentials are never
read from or written to repository files.
"""
from __future__ import annotations

from typing import Iterable, Any

from ..search_filters import SearchFilter, filter_hits
from ..search_index import SearchDocument, SearchEntity, SearchHit, normalize_query


class SupabaseSearchStore:
    """SearchStore-compatible adapter backed by two Supabase tables."""

    def __init__(self, client: Any, *, documents_table: str = "ocr_search_documents", entities_table: str = "ocr_search_entities") -> None:
        if client is None:
            raise ValueError("client must not be None")
        if not documents_table.strip() or not entities_table.strip():
            raise ValueError("table names must not be empty")
        self.client = client
        self.documents_table = documents_table
        self.entities_table = entities_table

    @classmethod
    def from_url_key(cls, url: str, key: str, **kwargs: Any) -> "SupabaseSearchStore":
        """Construct a client lazily; raises a clear error when dependency is absent."""
        if not url.strip() or not key.strip():
            raise ValueError("url and key must not be empty")
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError("Supabase adapter requires the optional 'supabase' package") from exc
        return cls(create_client(url, key), **kwargs)

    @staticmethod
    def _document_row(document: SearchDocument) -> dict[str, Any]:
        return {"document_id": document.document_id, "page_number": document.page_number, "block_id": document.block_id, "text": document.text}

    @staticmethod
    def _entity_row(entity: SearchEntity) -> dict[str, Any]:
        return {"document_id": entity.document_id, "entity_id": entity.entity_id, "entity_type": entity.entity_type, "value": entity.value, "page_number": entity.page_number, "block_id": entity.block_id, "confidence": entity.confidence}

    def upsert_document(self, document: SearchDocument) -> None:
        if not document.document_id.strip() or not document.block_id.strip():
            raise ValueError("document_id and block_id must not be empty")
        self.client.table(self.documents_table).upsert(self._document_row(document), on_conflict="document_id,page_number,block_id").execute()

    def upsert_entity(self, entity: SearchEntity) -> None:
        if not entity.document_id.strip() or not entity.entity_id.strip():
            raise ValueError("document_id and entity_id must not be empty")
        self.client.table(self.entities_table).upsert(self._entity_row(entity), on_conflict="document_id,entity_id").execute()

    def upsert_many(self, documents: Iterable[SearchDocument] = (), entities: Iterable[SearchEntity] = ()) -> None:
        document_rows = [self._document_row(d) for d in documents]
        entity_rows = [self._entity_row(e) for e in entities]
        if document_rows:
            self.client.table(self.documents_table).upsert(document_rows, on_conflict="document_id,page_number,block_id").execute()
        if entity_rows:
            self.client.table(self.entities_table).upsert(entity_rows, on_conflict="document_id,entity_id").execute()

    def search(self, query: str, *, limit: int = 20, search_filter: SearchFilter | None = None) -> tuple[SearchHit, ...]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        normalized = normalize_query(query)
        if not normalized:
            return ()
        # Postgres performs bounded candidate retrieval; final matching/ranking is
        # done in Python so Unicode normalization and deterministic ordering match
        # the in-memory/SQLite semantics.
        candidates = max(limit * 8, 32)
        entity_rows = self.client.table(self.entities_table).select("document_id,entity_id,entity_type,value,page_number,block_id,confidence").ilike("value", f"%{normalized}%").limit(candidates).execute().data or []
        text_rows = self.client.table(self.documents_table).select("document_id,page_number,block_id,text").ilike("text", f"%{normalized}%").limit(candidates).execute().data or []
        hits: list[SearchHit] = []
        for row in entity_rows:
            value = normalize_query(str(row["value"]))
            if normalized not in value:
                continue
            score, kind = (1.0, "exact_entity") if value == normalized else (0.92, "entity_contains")
            hits.append(SearchHit(str(row["document_id"]), int(row["page_number"]), str(row["block_id"]), kind, str(row["value"]), score, str(row["entity_id"]), str(row["entity_type"])))
        for row in text_rows:
            text = normalize_query(str(row["text"]))
            if normalized not in text:
                continue
            exact = text == normalized
            hits.append(SearchHit(str(row["document_id"]), int(row["page_number"]), str(row["block_id"]), "exact_text" if exact else "text_contains", str(row["text"]), 0.90 if exact else 0.82))
        hits.sort(key=lambda h: (-h.score, h.document_id, h.page_number, h.block_id, h.match_type, h.entity_id or ""))
        ranked = tuple(hits[:limit])
        return filter_hits(ranked, search_filter) if search_filter is not None else ranked

    def close(self) -> None:
        # Supabase clients do not require a connection close operation.
        return None


__all__ = ["SupabaseSearchStore"]
