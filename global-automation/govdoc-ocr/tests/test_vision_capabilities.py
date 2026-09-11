from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import available_backends, get_backend
from government_document import analyze_document
from search import search_documents
from language_packs.bihar_office_resolver import (
    find_district,
    find_education_terms,
    find_ocr_aliases,
    resolve_office,
)


def test_tesseract_backend_available():
    assert "tesseract" in available_backends()
    assert get_backend("tesseract").name == "tesseract"


def test_government_intelligence_is_evidence_based():
    result = analyze_document("बिहार विद्यालय परीक्षा समिति\nविषय: स्पॉट नामांकन हेतु सूचना\nदिनांक: 12.09.2026")
    assert result["authority"]["value"]
    assert "स्पॉट नामांकन" in result["subject"]["value"]
    assert result["document_type"]["value"] == "admission"


def test_keyword_search():
    docs = [{"id": "1", "text": "BSEB spot admission 2026", "metadata": {"district": "Gaya"}}]
    assert search_documents(docs, "BSEB admission")[0]["document_id"] == "1"


def test_bihar_education_vocabulary_and_ocr_aliases():
    text = "जिला शिक्षा पदाधिकारि, गया\nविषय: नामाकंन एवं परीक्षा\nविद्यालय में शौचालय की आवश्यकता"
    terms = find_education_terms(text)
    assert any(item["term"] == "नामांकन" for item in terms)
    assert any(item["term"] == "परीक्षा" for item in terms)
    assert any(item["term"] == "शौचालय" for item in terms)
    aliases = find_ocr_aliases(text)
    assert any(item["canonical"] == "नामांकन" and item["matched"] == "नामाकंन" for item in aliases)


def test_bihar_district_resolution_preserves_evidence():
    result = find_district("जिला शिक्षा पदाधिकारी, गया")
    assert result["key"] == "Gaya"
    assert result["matched"] == "गया"
    assert result["ambiguous"] is False


def test_ambiguous_bihar_districts_are_not_silently_canonicalized():
    result = find_district("आरा / Ara और भोजपुर")
    assert result["ambiguous"] is True
    assert set(result["candidates"]) == {"Bhojpur"}


def test_resolver_returns_context_without_guessing_from_names():
    result = resolve_office("प्रधानाध्यापक राम कुमार")
    assert result["district"] is None
    assert result["source_text_preserved"] is True
