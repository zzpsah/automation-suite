from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import available_backends, get_backend
from government_document import analyze_document
from search import search_documents
from language_packs.bihar_office_resolver import resolve_office


def _load_service_package():
    """Load the hyphenated govdoc-ocr directory under a stable package name."""
    if "govdoc_ocr" in sys.modules:
        return sys.modules["govdoc_ocr"]
    spec = importlib.util.spec_from_file_location(
        "govdoc_ocr",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules["govdoc_ocr"] = package
    assert spec.loader is not None
    spec.loader.exec_module(package)
    return package


def test_tesseract_backend_registered():
    assert "tesseract" in available_backends()
    assert get_backend("tesseract").name == "tesseract"


def test_government_intelligence_is_evidence_based():
    result = analyze_document(
        "बिहार विद्यालय परीक्षा समिति\n"
        "जिला शिक्षा पदाधिकारी, गया\n"
        "विषय: स्पॉट नामांकन हेतु सूचना\n"
        "दिनांक: 12.09.2026"
    )
    assert result["authority"]["value"]
    assert "स्पॉट नामांकन" in result["subject"]["value"]
    assert result["document_type"]["value"] == "admission"
    assert result["language_context"]["district"]["key"] == "Gaya"
    assert result["language_context"]["office"]["key"] == "deo"


def test_bihar_language_pack_resolves_domain_and_ocr_alias():
    result = resolve_office(
        "जिला शिक्षा पदाधिकारी, गया\n"
        "प्रखड शिक्षा पदाधिकारी\n"
        "विधालय में वार्षिक परिक्षा और नामाकंन"
    )
    assert result["district"]["key"] == "Gaya"
    assert result["office"]["key"] == "deo"
    aliases = {(item["canonical"], item["matched"]) for item in result["ocr_aliases"]}
    assert ("प्रखंड", "प्रखड") in aliases
    assert ("विद्यालय", "विधालय") in aliases
    assert ("परीक्षा", "परिक्षा") in aliases
    assert result["source_text_preserved"] is True


def test_ambiguous_district_is_not_guessed():
    result = resolve_office("गया और पटना जिला शिक्षा कार्यालय")
    assert result["district"]["ambiguous"] is True
    assert result["district"]["key"] is None
    assert set(result["district"]["candidates"]) == {"Gaya", "Patna"}


def test_keyword_search():
    docs = [{"id": "1", "text": "BSEB spot admission 2026", "metadata": {"district": "Gaya"}}]
    assert search_documents(docs, "BSEB admission")[0]["document_id"] == "1"


def test_image_ocr_end_to_end(tmp_path):
    """Exercise the real Tesseract path without B2, Supabase, or network data."""
    from PIL import Image, ImageDraw, ImageFont

    _load_service_package()
    from govdoc_ocr.ocr_service import process_image

    image_path = tmp_path / "sample.png"
    image = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
    font = ImageFont.truetype(font_path, 52)
    draw.text((60, 55), "शिक्षा विभाग", fill="black", font=font)
    draw.text((60, 135), "विद्यालय में नामांकन सूचना", fill="black", font=font)
    draw.text((60, 215), "Gaya District 2026", fill="black", font=font)
    image.save(image_path)

    result = process_image(str(image_path), str(tmp_path), backend="tesseract")
    text = result["text"]
    assert result["ocr"]["backend"] == "tesseract"
    assert "नामांकन" in result["normalized_text"] or "नामाकंन" in text
    assert result["pages"][0]["preprocessing"]["transformations"]
