from ocr.correction import correct_ocr_text


def test_label_variants_are_canonicalized():
    text = "विषयक : प्रवेश के संबंध में\nपत्र संख्या - 12/2026\nदिनांक - 25.06.2026"
    out = correct_ocr_text(text)
    assert "विषय: प्रवेश के संबंध में" in out
    assert "पत्रांक: 12/2026" in out
    assert "दिनांक: 25/06/2026" in out


def test_whitespace_is_conservative():
    text = "बिहार   विद्यालय\n\n परीक्षा समिति"
    assert correct_ocr_text(text) == "बिहार विद्यालय\n\nपरीक्षा समिति"


def test_empty_text():
    assert correct_ocr_text("") == ""
