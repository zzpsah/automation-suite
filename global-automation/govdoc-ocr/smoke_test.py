#!/usr/bin/env python3
"""Offline smoke test for GovDOC OCR metadata rules."""
from ocr_service import OCR_SERVICE_VERSION, _date, _metadata

assert OCR_SERVICE_VERSION == "2.0"
result = _metadata(
    "शिक्षा विभाग, बिहार सरकार\nपत्रांक: 123/2026\nदिनांक: 12.09.2026\nविषय: इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु सूचना",
    "notice.pdf",
)
assert result["authority"] == "शिक्षा विभाग, बिहार सरकार"
assert result["reference_number"] == "123/2026"
assert result["normalized_issue_date"] == "2026-09-12"
assert result["category_key"] == "admission"
assert _date("31.02.2026") is None
print("GovDOC OCR smoke test: PASS")
