#!/usr/bin/env python3
"""Offline smoke test for the canonical GovDOC Vision intelligence layer."""
from govdoc_ocr.government_document import analyze_document
from govdoc_ocr.sarkari_normalizer import normalize_sarkari_text

text = normalize_sarkari_text(
    "शिक्षा विभाग, बिहार सरकार\n"
    "पत्रांक: 123/2026\n"
    "दिनांक: 12.09.2026\n"
    "विषय: इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु सूचना"
)
result = analyze_document(text)

assert result["authority"]["value"] == "शिक्षा विभाग, बिहार सरकार"
assert "स्पॉट नामांकन" in result["subject"]["value"]
assert result["document_type"]["value"] == "admission"
assert result["evidence_policy"] == "source-backed; no invented metadata"
print("GovDOC Vision smoke test: PASS")
