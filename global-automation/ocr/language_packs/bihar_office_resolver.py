"""Evidence-based Bihar district/block office resolution helpers."""
from __future__ import annotations

import json
from pathlib import Path
import re

PACK = Path(__file__).with_name("bihar_districts.json")


def _load() -> dict:
    return json.loads(PACK.read_text(encoding="utf-8"))


def find_district(text: str) -> dict | None:
    """Find a district from explicit vocabulary evidence in source text."""
    value = text or ""
    pack = _load()
    matches = []
    for canonical, aliases in pack.get("districts", {}).items():
        for alias in aliases:
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", value, re.I):
                matches.append((canonical, alias))
    if not matches:
        return None
    # Prefer the longest explicit alias; this avoids short-name collisions.
    canonical, alias = max(matches, key=lambda item: len(item[1]))
    return {"key": canonical, "matched": alias, "source": "bihar_districts"}


def find_office_type(text: str) -> dict | None:
    """Identify an explicit education-office pattern; never infer from person names."""
    value = text or ""
    patterns = _load().get("office_patterns", {})
    priority = ["deo_office", "dpo_office", "beo_office", "rdd_office", "deo", "dpo", "beo", "rdd", "school"]
    for key in priority:
        for alias in patterns.get(key, []):
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", value, re.I):
                return {"key": key, "matched": alias, "source": "bihar_districts"}
    return None


def resolve_office(text: str) -> dict:
    """Return independently evidenced district and office information."""
    return {"district": find_district(text), "office": find_office_type(text)}
