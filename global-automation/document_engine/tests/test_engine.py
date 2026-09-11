from document_engine.classification import classify
from document_engine.confidence import score
from document_engine.extraction import extract


def test_classification_uses_evidence():
    assert classify("यह आदेश जारी किया जाता है") ["type"] == "order"


def test_extraction_does_not_invent_fields():
    result = extract("साधारण पाठ")
    assert result["reference"] is None
    assert result["date"] is None


def test_confidence_is_conservative():
    result = score("", {})
    assert result["level"] == "LOW"
