"""Evidence-based Bihar district/office resolution; never infer from names."""
from __future__ import annotations
import json, re
from pathlib import Path
PACK=Path(__file__).with_name("bihar_districts.json")
def _load(): return json.loads(PACK.read_text(encoding="utf-8"))
def find_district(text):
    matches=[]
    for canonical,aliases in _load().get("districts",{}).items():
        for alias in aliases:
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)",text or "",re.I): matches.append((canonical,alias))
    if not matches:return None
    canonical,alias=max(matches,key=lambda x:len(x[1])); return {"key":canonical,"matched":alias,"source":"bihar_districts"}
def find_office_type(text):
    for key,aliases in _load().get("office_patterns",{}).items():
        for alias in aliases:
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)",text or "",re.I): return {"key":key,"matched":alias,"source":"bihar_districts"}
    return None
def resolve_office(text): return {"district":find_district(text),"office":find_office_type(text)}
