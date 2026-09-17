import json
from pathlib import Path

from ocr.training.promote_pack import promote


def test_promotion_creates_new_version_without_mutating_source(tmp_path):
    source = tmp_path / "pack.json"
    source.write_text(json.dumps({"name": "test", "version": "0.2.0", "aliases": {}}), encoding="utf-8")
    candidates = tmp_path / "candidates.json"
    candidates.write_text(json.dumps([
        {"observed": "विधालय", "correction": "विद्यालय", "frequency": 3, "review_status": "approved"},
        {"observed": "एकबार", "correction": "एक बार", "frequency": 1, "review_status": "approved"},
    ], ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "new.json"
    report = promote(str(source), str(candidates), str(output))
    assert report["to"] == "0.2.1"
    assert report["applied"] == 1
    assert json.loads(source.read_text(encoding="utf-8"))["version"] == "0.2.0"
    assert json.loads(output.read_text(encoding="utf-8"))["aliases"]["विधालय"] == "विद्यालय"
