from ocr.subject_extractor import extract_multiline_subject


def test_multiline_subject():
    text = "विषय: सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में\nस्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में\nदिनांक: 25/06/2026"
    assert extract_multiline_subject(text) == "सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में"


def test_subject_stops_before_copy_to():
    text = "विषय: विद्यालय संबंधी महत्वपूर्ण सूचना\nप्रतिलिपि: जिला शिक्षा पदाधिकारी\nकार्यालय: जिला कार्यालय"
    assert extract_multiline_subject(text) == "विद्यालय संबंधी महत्वपूर्ण सूचना"


def test_missing_subject():
    assert extract_multiline_subject("दिनांक: 01/09/2026\nपत्रांक: 2/2026") is None
