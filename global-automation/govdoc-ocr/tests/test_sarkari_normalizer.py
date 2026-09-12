from __future__ import annotations

from sarkari_normalizer import normalize_sarkari_text


def test_bihar_ocr_aliases_and_unicode_are_canonicalized():
    text = "जिला शिक्शा पदाधिकारि, गया\nविद्यलय में कार्यभार ग्रहन की तिथि 12 . 09 . 2026"
    result = normalize_sarkari_text(text)
    assert "जिला शिक्षा पदाधिकारी" in result
    assert "विद्यालय" in result
    assert "कार्यभार ग्रहण" in result
    assert "12/09/2026" in result


def test_administrative_phrasing_is_grammatically_normalized_without_invention():
    text = "उपरोक्त विषयक के सम्बन्ध मे आवश्यक कार्यवाही करें।"
    result = normalize_sarkari_text(text)
    assert result == "उपरोक्त विषय के संबंध में आवश्यक कार्रवाई करें."


def test_official_labels_are_normalized():
    text = "विषयः शिक्षक स्थानान्तरण\nपत्र संख्या : 1234\nदिनांकित 12-09-2026"
    result = normalize_sarkari_text(text)
    assert "विषय:" in result
    assert "पत्रांक: 1234" in result
    assert "दिनांक: 12/09/2026" in result


def test_normalizer_does_not_invent_missing_content():
    source = "पत्रांक 1234\nशिक्षक"
    result = normalize_sarkari_text(source)
    assert "1234" in result
    assert "शिक्षक" in result
    assert "स्थानांतरण" not in result
