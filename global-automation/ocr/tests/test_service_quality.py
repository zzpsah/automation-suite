from ocr.ocr_service import score_metadata_quality


def test_quality_requires_evidence():
    metadata = {
        "subject": "महत्वपूर्ण सरकारी सूचना",
        "authority": "बिहार विद्यालय परीक्षा समिति",
        "reference_number": "123/2026",
        "issue_date": "2026-06-25",
    }
    result = score_metadata_quality(metadata, "महत्वपूर्ण सरकारी सूचना बिहार विद्यालय परीक्षा समिति 123/2026 2026-06-25")
    assert result["level"] == "HIGH"
    assert result["score"] == 1.0


def test_empty_or_unverifiable_metadata_is_low():
    metadata = {
        "subject": "यह विषय है",
        "authority": "काल्पनिक कार्यालय",
        "reference_number": "999",
        "issue_date": "2026-01-01",
    }
    result = score_metadata_quality(metadata, "असंबंधित OCR text")
    assert result["level"] == "LOW"
    assert result["score"] == 0
