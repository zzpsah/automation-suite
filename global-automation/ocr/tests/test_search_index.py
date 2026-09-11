from ocr.document_understanding import UnderstandingEntity, DocumentUnderstandingGraph
from ocr.search_index import SearchDocument, build_search_index, normalize_query, search_to_dict


def graph(*entities):
    return DocumentUnderstandingGraph(tuple(entities), ())


def entity(entity_id, entity_type, value, page=1, block="b1", confidence=0.9):
    return UnderstandingEntity(entity_id, entity_type, value, page, block, confidence)


def test_normalize_query_is_unicode_safe_and_non_mutating():
    assert normalize_query("  पत्रांक   REF-123  ") == "पत्रांक ref-123"


def test_exact_entity_match_returns_provenance():
    index = build_search_index({"doc-a": graph(entity("e1", "reference", "REF-123"))})
    hits = index.search("ref-123")
    assert hits[0].match_type == "exact_entity"
    assert hits[0].document_id == "doc-a"
    assert hits[0].page_number == 1
    assert hits[0].block_id == "b1"
    assert hits[0].entity_id == "e1"


def test_text_search_and_entity_search_can_coexist():
    index = build_search_index(
        {"doc-a": graph(entity("e1", "authority", "District Education Officer"))},
        {"doc-a": [SearchDocument("doc-a", 2, "b2", "seniority determination REF-123")]},
    )
    hits = index.search("REF-123")
    assert hits[0].match_type == "text_contains"
    assert hits[0].document_id == "doc-a"
    assert hits[0].page_number == 2


def test_unrelated_document_does_not_match():
    index = build_search_index({"doc-a": graph(entity("e1", "reference", "REF-123")), "doc-b": graph(entity("e2", "reference", "REF-999"))})
    assert [hit.document_id for hit in index.search("REF-777")] == []


def test_limit_and_deterministic_serialization():
    index = build_search_index({"doc-b": graph(entity("e2", "reference", "REF-123")), "doc-a": graph(entity("e1", "reference", "REF-123"))})
    hits = index.search("REF-123", limit=1)
    assert len(hits) == 1
    assert hits[0].document_id == "doc-a"
    assert search_to_dict(hits)[0]["entity_id"] == "e1"
    assert index.to_dict()["entities"][0]["document_id"] == "doc-a"


def test_invalid_limit_fails_closed():
    index = build_search_index({})
    try:
        index.search("x", limit=0)
    except ValueError as exc:
        assert "limit" in str(exc)
    else:
        raise AssertionError("expected ValueError")
