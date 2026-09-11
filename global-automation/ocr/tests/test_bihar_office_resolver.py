from ocr.language_packs.bihar_office_resolver import find_district, find_office_type, resolve_office


def test_explicit_siwan_district():
    result = find_district("जिला शिक्षा पदाधिकारी, सिवान")
    assert result["key"] == "Siwan"
    assert result["matched"] == "सिवान"


def test_office_priority_prefers_specific_office():
    result = find_office_type("जिला शिक्षा पदाधिकारी कार्यालय, सिवान")
    assert result["key"] == "deo_office"


def test_no_unsafe_inference():
    assert resolve_office("पत्र प्राप्त हुआ। नाम: Siwan Kumar") ["district"] is None
