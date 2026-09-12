from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "language_packs" / "bihar_education.json"
CORPUS = ROOT / "language_packs" / "test_bihar_education.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _flatten_terms(pack: dict) -> set[str]:
    terms: set[str] = set()
    for values in pack.get("domains", {}).values():
        terms.update(values)
    terms.update(pack.get("ocr_aliases", {}).keys())
    for aliases in pack.get("ocr_aliases", {}).values():
        terms.update(aliases)
    return terms


def test_bihar_education_pack_is_valid_and_versioned():
    pack = _load(PACK)
    assert pack["locale"] == "hi-IN"
    assert pack["version"] == "0.4.0"
    assert pack["domains"]
    assert pack["ocr_aliases"]
    assert pack["safety"]["preserve_original_text"] is True


def test_benchmark_corpus_terms_are_covered():
    pack = _load(PACK)
    corpus = _load(CORPUS)
    terms = _flatten_terms(pack)
    missing: list[tuple[str, str]] = []
    for case in corpus["cases"]:
        for expected in case["expected_terms"]:
            if expected not in terms:
                missing.append((case["id"], expected))
    assert not missing, f"language-pack benchmark terms missing: {missing}"


def test_aliases_do_not_replace_canonical_text():
    pack = _load(PACK)
    aliases = pack["ocr_aliases"]
    for canonical, variants in aliases.items():
        assert canonical in variants
        assert canonical in _flatten_terms(pack)
