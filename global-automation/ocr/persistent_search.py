"""Storage adapters for the global OCR search contract.

The core OCR/search layer stays storage-agnostic. SQLite is provided as a small,
portable persistent adapter; external databases can implement the same contract
without changing OCR or consumer code.
"""
from __future__ import annotations

import sqlite3
from typing import Iterable

from .search_index import SearchDocument, SearchEntity, SearchHit, normalize_query


class SQLiteSearchStore:
    """Persistent SQLite adapter for SearchDocument/SearchEntity records."""

    def __init__(self, path: str) -> None:
        if not path.strip():
            raise ValueError("path must not be empty")
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS search_documents (
                document_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                block_id TEXT NOT NULL,
                text TEXT NOT NULL,
                PRIMARY KEY (document_id, page_number, block_id)
            );
            CREATE TABLE IF NOT EXISTS search_entities (
                document_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                value TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                block_id TEXT NOT NULL,
                confidence REAL NOT NULL,
                PRIMARY KEY (document_id, entity_id)
            );
            CREATE INDEX IF NOT EXISTS idx_search_entities_normalized
                ON search_entities(entity_type, value);
            CREATE INDEX IF NOT EXISTS idx_search_documents_text
                ON search_documents(text);
            """
        )
        self.connection.commit()

    @staticmethod
    def _validate_document(document: SearchDocument) -> None:
        if not document.document_id.strip() or not document.block_id.strip():
            raise ValueError("document_id and block_id must not be empty")

    @staticmethod
    def _validate_entity(entity: SearchEntity) -> None:
        if not entity.document_id.strip() or not entity.entity_id.strip():
            raise ValueError("document_id and entity_id must not be empty")

    def upsert_document(self, document: SearchDocument) -> None:
        self._validate_document(document)
        self.connection.execute(
            """INSERT INTO search_documents(document_id,page_number,block_id,text)
               VALUES(?,?,?,?)
               ON CONFLICT(document_id,page_number,block_id)
               DO UPDATE SET text=excluded.text""",
            (document.document_id, document.page_number, document.block_id, document.text),
        )
        self.connection.commit()

    def upsert_entity(self, entity: SearchEntity) -> None:
        self._validate_entity(entity)
        self.connection.execute(
            """INSERT INTO search_entities
               (document_id,entity_id,entity_type,value,page_number,block_id,confidence)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(document_id,entity_id)
               DO UPDATE SET entity_type=excluded.entity_type,value=excluded.value,
                             page_number=excluded.page_number,block_id=excluded.block_id,
                             confidence=excluded.confidence""",
            (entity.document_id, entity.entity_id, entity.entity_type, entity.value,
             entity.page_number, entity.block_id, entity.confidence),
        )
        self.connection.commit()

    def upsert_many(self, documents: Iterable[SearchDocument] = (), entities: Iterable[SearchEntity] = ()) -> None:
        with self.connection:
            for document in documents:
                self._validate_document(document)
                self.connection.execute(
                    """INSERT INTO search_documents(document_id,page_number,block_id,text)
                       VALUES(?,?,?,?) ON CONFLICT(document_id,page_number,block_id)
                       DO UPDATE SET text=excluded.text""",
                    (document.document_id, document.page_number, document.block_id, document.text),
                )
            for entity in entities:
                self._validate_entity(entity)
                self.connection.execute(
                    """INSERT INTO search_entities
                       (document_id,entity_id,entity_type,value,page_number,block_id,confidence)
                       VALUES(?,?,?,?,?,?,?) ON CONFLICT(document_id,entity_id)
                       DO UPDATE SET entity_type=excluded.entity_type,value=excluded.value,
                       page_number=excluded.page_number,block_id=excluded.block_id,confidence=excluded.confidence""",
                    (entity.document_id, entity.entity_id, entity.entity_type, entity.value,
                     entity.page_number, entity.block_id, entity.confidence),
                )

    def search(self, query: str, *, limit: int = 20) -> tuple[SearchHit, ...]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        normalized = normalize_query(query)
        if not normalized:
            return ()
        pattern = f"%{normalized}%"
        rows = self.connection.execute(
            """SELECT document_id,entity_id,entity_type,value,page_number,block_id,confidence
               FROM search_entities WHERE lower(trim(value)) LIKE ?
               ORDER BY document_id,page_number,block_id,entity_id LIMIT ?""",
            (pattern, limit * 4),
        ).fetchall()
        hits: list[SearchHit] = []
        for row in rows:
            value = normalize_query(row["value"])
            if normalized not in value:
                continue
            if value == normalized:
                score, kind = 1.0, "exact_entity"
            else:
                score, kind = 0.92, "entity_contains"
            hits.append(SearchHit(row["document_id"], row["page_number"], row["block_id"], kind,
                                  row["value"], score, row["entity_id"], row["entity_type"]))
        text_rows = self.connection.execute(
            """SELECT document_id,page_number,block_id,text FROM search_documents
               WHERE lower(trim(text)) LIKE ?
               ORDER BY document_id,page_number,block_id LIMIT ?""",
            (pattern, limit * 4),
        ).fetchall()
        for row in text_rows:
            text = normalize_query(row["text"])
            if normalized not in text:
                continue
            hits.append(SearchHit(row["document_id"], row["page_number"], row["block_id"],
                                  "exact_text" if text == normalized else "text_contains",
                                  row["text"], 0.90 if text == normalized else 0.82))
        hits.sort(key=lambda h: (-h.score, h.document_id, h.page_number, h.block_id, h.match_type, h.entity_id or ""))
        return tuple(hits[:limit])

    def export(self) -> dict:
        documents = [dict(row) for row in self.connection.execute(
            "SELECT document_id,page_number,block_id,text FROM search_documents ORDER BY document_id,page_number,block_id"
        )]
        entities = [dict(row) for row in self.connection.execute(
            "SELECT document_id,entity_id,entity_type,value,page_number,block_id,confidence FROM search_entities ORDER BY document_id,page_number,block_id,entity_id"
        )]
        return {"documents": documents, "entities": entities}

    def close(self) -> None:
        self.connection.close()


__all__ = ["SQLiteSearchStore"]
