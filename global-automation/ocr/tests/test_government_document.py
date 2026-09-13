from ocr.government_document import analyze_document


def test_bihar_letter_header_subject_and_action():
    text = """बिहार विद्यालय परीक्षा समिति
विषय: सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में
दिनांक: 25.06.2026

1. एतद् द्वारा राज्य के इंटरमीडिएट स्तर के शिक्षण संस्थानों को सूचित किया जाता है।
2. स्पॉट नामांकन की तिथि दिनांक 15.09.2026 से 18.09.2026 तक अंतिम रूप से विस्तारित की जाती है।
"""
    result = analyze_document(text)
    assert result["authority"]["value"] == "बिहार विद्यालय परीक्षा समिति"
    assert "स्पॉट नामांकन" in result["subject"]["value"]
    assert result["subject"]["source"] == "subject_label"
    assert result["document_type"]["value"] == "admission"
    assert "18.09.2026" in result["deadlines"]
    assert result["short_description"]


def test_body_reference_does_not_replace_header_authority():
    text = """शिक्षा विभाग, बिहार
विषय: विद्यालयों के लिए आवश्यक निर्देश

1. बिहार विद्यालय परीक्षा समिति की विज्ञप्ति के अनुसार विद्यार्थियों को सूचित किया जाता है।
"""
    result = analyze_document(text)
    assert result["authority"]["value"] == "शिक्षा विभाग, बिहार"
    assert result["subject"]["value"] == "विद्यालयों के लिए आवश्यक निर्देश"
