from ocr.document_understanding import DocumentUnderstandingGraph, UnderstandingEntity
from ocr.search_index import DocumentSearchIndex, SearchDocument, build_search_index, search_to_dict


def entity(entity_id, kind, value, page=1, block="b1", confidence=0.9):
    return UnderstandingEntity(entity_id, kind, value, page, block, confidence)


def test_exact_entity_search_ranks_first_and_preserves_provenance():
    index = DocumentSearchIndex()
    index.add_entity("doc-2", entity("r2", "reference", "REF/123", 2, "block-7"))
    index.add_entity("doc-1", entity("r1", "reference", "REF/123", 1, "block-3"))
    hits = index.search(" ref/123 ")
    assert hits[0].match_type == "exact_entity"
    assert hits[0].document_id == "doc-1"
    assert hits[0].page_number == 1
    assert hits[0].block_id == "block-3"
    assert hits[0].entity_id == "r1"


def test_hindi_and_casefolded_text_are_searchable():
    index = DocumentSearchIndex()
    index.add_document(SearchDocument("doc-1", 1, "b1", "जिला शिक्षा पदाधिकारी, Gaya"))
    hits = index.search("जिला शिक्षा")
    assert hits
    assert hits[0].document_id == "doc-1"
    assert hits[0].match_type == "text_contains"


def test_build_index_from_understanding_graphs():
    graph = DocumentUnderstandingGraph((entity("r1", "reference", "पत्रांक-42", 1, "b1"),), ())
    index = build_search_index({"doc-1": graph})
    hits = index.search("पत्रांक-42")
    assert len(hits) == 1
    assert hits[0].entity_type == "reference"


def test_limit_and_empty_query_are_deterministic():
    index = DocumentSearchIndex()
    index.add_document(SearchDocument("doc-1", 1, "b1", "notice notice"))
    index.add_document(SearchDocument("doc-2", 1, "b1", "notice"))
    assert index.search("", limit=2) == ()
    assert len(index.search("notice", limit=1)) == 1


def test_search_serialization_is_json_compatible():
    index = DocumentSearchIndex()
    index.add_entity("doc-1", entity("e1", "reference", "REF-1"))
    payload = search_to_dict(index.search("REF-1"))
    assert payload[0]["document_id"] == "doc-1"
    assert payload[0]["entity_id"] == "e1"
