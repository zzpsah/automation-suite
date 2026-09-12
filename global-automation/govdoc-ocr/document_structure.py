"""Conservative document structure signals from OCR regions/text."""
from __future__ import annotations
import re
from .regions import OCRRegion, regions_to_dict
from .layout import group_lines

_HEADING_RE = re.compile(r"^(?:[0-9]+[.)]|[क-ह][.)]|[A-Z][.)]|विषय|Subject|क्रमांक|दिनांक|सेवा में|प्रति|आदेश|सूचना)\b", re.I)


def classify_region(region: OCRRegion | dict) -> str:
    """Classify only strong lexical/layout signals; otherwise return body."""
    r = region.to_dict() if isinstance(region, OCRRegion) else region
    text = (r.get("text") or "").strip()
    if not text:
        return "unknown"
    if _HEADING_RE.search(text):
        return "heading_signal"
    return "body"


def structure_evidence(regions: list[OCRRegion | dict]) -> dict:
    normalized = regions_to_dict(regions)
    lines = group_lines(normalized)
    items = [{"id": r["id"], "kind": classify_region(r)} for r in normalized]
    return {
        "region_count": len(normalized),
        "line_count": len(lines),
        "items": items,
        "signals": {
            "heading_signals": sum(i["kind"] == "heading_signal" for i in items),
            "has_body": any(i["kind"] == "body" for i in items),
        },
        "evidence_only": True,
    }
