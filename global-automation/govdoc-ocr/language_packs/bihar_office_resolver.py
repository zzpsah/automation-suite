"""Evidence-based Bihar language resolver for OCR and government documents.

The resolver returns evidence, not guesses. Ambiguous matches stay ambiguous and
source wording is never replaced by a canonical value.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

PACK = Path(__file__).with_name("bihar_districts.json")
EDU_PACK = Path(__file__).with_name("bihar_education.json")

def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def _norm(text: str) -> str:
    value = text or ""
    for source, target in _load(EDU_PACK).get("normalization", {}).get("unicode_equivalents", {}).items():
        value = value.replace(source, target)
    value = re.sub(r"[ \t\r\n]+", " ", value)
    return value.strip()

def _matches(text: str, canonical: str, aliases: list[str]) -> list[dict]:
    found = []
    for alias in aliases:
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.I):
            found.append({"key": canonical, "matched": alias})
    return found

def find_district(text: str):
    value = _norm(text)
    matches = []
    for canonical, aliases in _load(PACK).get("districts", {}).items():
        matches.extend(_matches(value, canonical, aliases))
    if not matches:
        return None
    unique = {(m["key"], m["matched"]): m for m in matches}
    matches = list(unique.values())
    keys = sorted({m["key"] for m in matches})
    if len(keys) > 1:
        return {"key": None, "matched": [m["matched"] for m in matches], "source": "bihar_districts", "ambiguous": True, "candidates": keys}
    best = max(matches, key=lambda item: len(item["matched"]))
    return {"key": best["key"], "matched": best["matched"], "source": "bihar_districts", "ambiguous": False}

def find_office_type(text: str):
    value = _norm(text)
    matches = []
    for key, aliases in _load(PACK).get("office_patterns", {}).items():
        matches.extend(_matches(value, key, aliases))
    if not matches:
        return None
    keys = sorted({m["key"] for m in matches})
    if len(keys) > 1:
        return {"key": None, "matched": [m["matched"] for m in matches], "source": "bihar_districts", "ambiguous": True, "candidates": keys}
    best = max(matches, key=lambda item: len(item["matched"]))
    return {"key": best["key"], "matched": best["matched"], "source": "bihar_districts", "ambiguous": False}

def find_education_terms(text: str) -> list[dict]:
    value = _norm(text)
    found = []
    for domain, terms in _load(EDU_PACK).get("domains", {}).items():
        for term in terms:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", value, re.I):
                found.append({"term": term, "domain": domain, "source": "bihar_education"})
    return found

def find_ocr_aliases(text: str) -> list[dict]:
    value = _norm(text)
    found = []
    for canonical, aliases in _load(EDU_PACK).get("ocr_aliases", {}).items():
        for alias in aliases:
            if alias != canonical and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", value, re.I):
                found.append({"canonical": canonical, "matched": alias, "source": "bihar_education", "safe_to_suggest": True})
    return found

def resolve_office(text: str):
    return {"district": find_district(text), "office": find_office_type(text), "education_terms": find_education_terms(text), "ocr_aliases": find_ocr_aliases(text), "source_text_preserved": True}
