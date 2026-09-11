from ocr.search_index import normalize_query

def test_placeholder():
    assert normalize_query(" REF-123 ") == "ref-123"
