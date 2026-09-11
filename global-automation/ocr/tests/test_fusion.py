from global_automation.ocr.fusion import consensus
from global_automation.ocr.backend import OCRResult


def test_consensus_selects_majority_and_reports_agreement():
    result = consensus([
        OCRResult("सरकारी आदेश", "tesseract", 0.8),
        OCRResult("सरकारी आदेश", "paddleocr", 0.9),
        OCRResult("सरकार आदेश", "other", 0.7),
    ])
    assert result.text == "सरकारी आदेश"
    assert result.agreeing_backends == ("paddleocr", "tesseract")
    assert result.disagreement is True
    assert result.confidence == 0.85


def test_consensus_is_deterministic_on_tie():
    result = consensus([
        OCRResult("B", "tesseract"),
        OCRResult("A", "paddleocr"),
    ])
    assert result.text == "A"
    assert result.disagreement is True


def test_consensus_rejects_empty_results():
    try:
        consensus([])
    except ValueError as exc:
        assert "No OCR results" in str(exc)
    else:
        raise AssertionError("empty consensus must fail closed")
