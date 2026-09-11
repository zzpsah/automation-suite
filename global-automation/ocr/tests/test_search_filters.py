import json

import pytest

from ocr.search_filters import SearchFilter, filter_hits, filter_to_dict
from ocr.search_index import SearchHit


def hit(document_id, page, block, score, entity_type=None):
    return SearchHit(document_id, page, block, "entity", "value", score, "e1", entity_type)


def test_filter_preserves_order_and_provenance():
    hits = (
        hit("a", 2, "b2", 0.9, "reference"),
        hit("b", 1, "b1", 0.8, "date"),
        hit("a", 1, "b1", 0.7, "reference"),
    )
    result = filter_hits(hits, SearchFilter(document_ids=frozenset({"a"}), entity_types=frozenset({"reference"})))
    assert result == (hits[0], hits[2])
    assert result[0].document_id == "a"
    assert result[0].page_number == 2


def test_filters_can_target_page_block_and_score():
    hits = (hit("a", 1, "b1", 0.4), hit("a", 2, "b2", 0.8))
    result = filter_hits(hits, SearchFilter(page_numbers=frozenset({2}), block_ids=frozenset({"b2"}), min_score=0.8))
    assert result == (hits[1],)


def test_empty_filter_is_identity():
    hits = (hit("a", 1, "b1", 0.5),)
    assert filter_hits(hits, SearchFilter()) == hits


def test_filter_validation_and_json_safe_serialization():
    with pytest.raises(ValueError):
        SearchFilter(min_score=1.1)
    payload = filter_to_dict(SearchFilter(document_ids=frozenset({"b", "a"}), page_numbers=frozenset({2, 1})))
    assert payload["document_ids"] == ["a", "b"]
    assert payload["page_numbers"] == [1, 2]
    json.dumps(payload)
