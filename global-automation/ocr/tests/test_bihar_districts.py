import json
from pathlib import Path

PACK = Path(__file__).parents[1] / "language_packs" / "bihar_districts.json"


def test_bihar_has_38_districts():
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    assert len(pack["districts"]) == 38


def test_key_bihar_district_aliases():
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    assert "सिवान" in pack["districts"]["Siwan"]
    assert "सारण" in pack["districts"]["Saran"]
    assert "पूर्वी चंपारण" in pack["districts"]["East Champaran"]
    assert "Bhabua" in pack["districts"]["Kaimur"]


def test_office_patterns_cover_core_education_offices():
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    for key in ("deo", "dpo", "beo", "rdd", "school", "school_code"):
        assert pack["office_patterns"][key]
