import json
from pathlib import Path


PACK = Path(__file__).parents[1] / "language_packs" / "bihar_education.json"


def load_pack():
    return json.loads(PACK.read_text(encoding="utf-8"))


def test_pack_version_and_core_authorities():
    pack = load_pack()
    assert pack["version"] == "0.2.0"
    assert "बिहार विद्यालय परीक्षा समिति" in pack["authorities"]
    assert "जिला शिक्षा पदाधिकारी" in pack["authorities"]
    assert pack["authority_aliases"]["BSEB"] == "बिहार विद्यालय परीक्षा समिति"


def test_current_education_terms_are_present():
    pack = load_pack()
    assert "ई-शिक्षाकोष" in pack["document_types"]["digital_record"]
    assert "विद्यालय निरीक्षण" in pack["document_types"]["inspection"]
    assert "मध्याह्न भोजन योजना" in pack["document_types"]["mid_day_meal"]
    assert "शिक्षकेतर कर्मी" in pack["education_terms"]["school_staff"]


def test_safe_normalization_rules():
    pack = load_pack()
    rules = pack["normalization_rules"]
    assert rules["preserve_source_text"] is True
    assert rules["do_not_invent_fields"] is True
    assert rules["do_not_replace_official_names_without_evidence"] is True
