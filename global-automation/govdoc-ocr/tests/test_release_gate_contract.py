"""Release-gate contract tests for representative structural outputs."""
from __future__ import annotations

from govdoc_ocr.release_gate import validate_result


def _valid_result():
    return {
        "schema_version": "1.1",
        "text": "Government notice",
        "normalized_text": "Government notice",
        "filename": "notice.pdf",
        "pages": [
            {"page_number": 1, "text": "Government notice", "regions": []},
            {"page_number": 2, "text": "Second page", "regions": []},
        ],
        "ocr": {"backend": "tesseract"},
    }


def test_release_gate_accepts_valid_result():
    report = validate_result(_valid_result())
    assert report["valid"] is True
    assert report["checks"] == {"required_keys": True, "page_order": True}


def test_release_gate_rejects_missing_required_key():
    result = _valid_result()
    result.pop("ocr")
    report = validate_result(result)
    assert report["valid"] is False
    assert "ocr" in report["missing_keys"]


def test_release_gate_rejects_non_sequential_pages():
    result = _valid_result()
    result["pages"][1]["page_number"] = 3
    report = validate_result(result)
    assert report["valid"] is False
    assert report["sequential_pages"] is False
