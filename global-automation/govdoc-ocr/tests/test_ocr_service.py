from govdoc_ocr.ocr_service import OCR_SERVICE_VERSION, _date, _metadata


def test_version_is_present():
    assert OCR_SERVICE_VERSION == "2.0"


def test_hindi_government_metadata():
    text = """शिक्षा विभाग, बिहार सरकार
पत्रांक: 123/2026
दिनांक: 12.09.2026
विषय: इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु सूचना
"""
    result = _metadata(text, "notice.pdf")
    assert result["subject"].startswith("इंटरमीडिएट")
    assert result["authority"] == "शिक्षा विभाग, बिहार सरकार"
    assert result["reference_number"] == "123/2026"
    assert result["issue_date"] == "12.09.2026"
    assert result["normalized_issue_date"] == "2026-09-12"
    assert result["category_key"] == "admission"


def test_invalid_date_fails_closed():
    assert _date("31.02.2026") is None
