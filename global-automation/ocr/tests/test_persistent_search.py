import json

from ocr.persistent_search import SQLiteSearchStore
from ocr.search_index import SearchDocument, SearchEntity


def entity(document_id, entity_id, value):
    return SearchEntity(document_id, entity_id, "reference", value, 1, "b1", 0.9)


def test_sqlite_store_upserts_and_searches(tmp_path):
    store = SQLiteSearchStore(str(tmp_path / "search.db"))
    store.upsert_many(
        documents=[SearchDocument("doc-1", 1, "b1", "Order REF-123")],
        entities=[entity("doc-1", "r1", "REF-123")],
    )
    hits = store.search(" ref-123 ")
    assert hits[0].match_type == "exact_entity"
    assert hits[0].document_id == "doc-1"
    assert hits[0].entity_id == "r1"
    store.close()


def test_upsert_replaces_source_without_duplicate_rows(tmp_path):
    store = SQLiteSearchStore(str(tmp_path / "search.db"))
    document = SearchDocument("doc-1", 1, "b1", "old")
    store.upsert_document(document)
    store.upsert_document(SearchDocument("doc-1", 1, "b1", "new"))
    exported = store.export()
    assert exported["documents"] == [{"document_id": "doc-1", "page_number": 1, "block_id": "b1", "text": "new"}]
    store.close()


def test_export_is_json_serializable(tmp_path):
    store = SQLiteSearchStore(str(tmp_path / "search.db"))
    store.upsert_entity(entity("doc-1", "r1", "REF-1"))
    json.dumps(store.export())
    store.close()


def test_empty_query_and_invalid_limit(tmp_path):
    store = SQLiteSearchStore(str(tmp_path / "search.db"))
    assert store.search("") == ()
    try:
        store.search("x", limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    store.close()
