from ocr.document_understanding import DocumentUnderstandingGraph, UnderstandingEntity
from ocr.search_index import SearchDocument, build_search_index, normalize_query


def graph(*entities):
    return DocumentUnderstandingGraph(tuple(entities), ())


def entity(i, typ, value, page=1, block="b1"):
    return UnderstandingEntity(i, typ, value, page, block, 0.9)


def test_unicode_exact_entity_and_provenance():
    index = build_search_index({"a": graph(entity("e1", "reference", "REF-123"))})
    hits = index.search("  ref-123 ")
    assert normalize_query("  पत्रांक   REF-123 ") == "पत्रांक ref-123"
    assert hits[0].match_type == "exact_entity"
    assert (hits[0].document_id, hits[0].page_number, hits[0].block_id, hits[0].entity_id) == ("a", 1, "b1", "e1")


def test_text_contains_and_entity_search():
    index = build_search_index(
        {"a": graph(entity("e1", "authority", "District Education Officer"))},
        {"a": [SearchDocument("a", 2, "b2", "seniority determination REF-123")]},
    )
    hits = index.search("REF-123")
    assert hits[0].match_type == "text_contains"
    assert hits[0].page_number == 2


def test_unrelated_document_does_not_match():
    index = build_search_index({"a": graph(entity("e1", "reference", "REF-123")), "b": graph(entity("e2", "reference", "REF-999"))})
    assert index.search("REF-777") == ()


def test_deterministic_limit_and_serialization():
    index = build_search_index({"b": graph(entity("e2", "reference", "REF-123")), "a": graph(entity("e1", "reference", "REF-123"))})
    hits = index.search("REF-123", limit=1)
    assert len(hits) == 1 and hits[0].document_id == "a"
    assert index.to_dict()["entities"][0]["document_id"] == "a"


def test_invalid_limit_fails_closed():
    index = build_search_index({})
    try:
        index.search("x", limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
