import json

from ocr.pack_loader import load_pack, list_packs


def test_load_pack_and_list(tmp_path):
    (tmp_path / "demo.json").write_text(json.dumps({"name": "Demo", "version": "1.0.0"}), encoding="utf-8")
    assert load_pack("demo", tmp_path)["version"] == "1.0.0"
    assert list_packs(tmp_path) == ["demo"]
