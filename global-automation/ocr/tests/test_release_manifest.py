from pathlib import Path

import pytest

from ocr.release_manifest import build_release_manifest, manifest_to_json, verify_release_manifest


def test_manifest_is_deterministic_and_verifiable(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("B", encoding="utf-8")
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")
    manifest = build_release_manifest(tmp_path, "1.2.3", ["b.txt", "a.txt"])
    assert [x.path for x in manifest.files] == ["a.txt", "b.txt"]
    assert verify_release_manifest(tmp_path, manifest) == (True, ())
    assert manifest_to_json(manifest).count("sha256") == 2


def test_manifest_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("A", encoding="utf-8")
    manifest = build_release_manifest(tmp_path, "1.0.0", ["a.txt"])
    path.write_text("tampered", encoding="utf-8")
    ok, errors = verify_release_manifest(tmp_path, manifest)
    assert not ok
    assert "sha256_mismatch:a.txt" in errors


def test_manifest_rejects_invalid_version_or_escape(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")
    with pytest.raises(ValueError):
        build_release_manifest(tmp_path, "1.0", ["a.txt"])
    with pytest.raises(ValueError):
        build_release_manifest(tmp_path, "1.0.0", ["../outside"])
