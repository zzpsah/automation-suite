"""Conservative multi-line subject extraction for government documents."""
from __future__ import annotations

import re

SUBJECT_LABEL = re.compile(r"^\s*(?:विषय|विषयक|subject|sub\.)\s*[:：\-–—]?\s*(.*)$", re.I)
STOP_LABELS = re.compile(r"^\s*(?:पत्रांक|ज्ञापांक|क्रमांक|दिनांक|कार्यालय|विभाग|प्रेषक|प्रतिलिपि|प्रति|संलग्न|encl\.?|copy to|from|office|department)\b", re.I)


def extract_multiline_subject(text: str, max_lines: int = 6, max_chars: int = 1200) -> str | None:
    """Extract a subject that may continue over several OCR lines.

    Stops at another administrative field/footer and never invents text.
    """
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in (text or "").splitlines()]
    for i, line in enumerate(lines):
        match = SUBJECT_LABEL.match(line)
        if not match:
            continue
        first = match.group(1).strip(" :-–—")
        parts = [first] if first else []
        for nxt in lines[i + 1 : i + 1 + max_lines - 1]:
            if not nxt:
                if parts:
                    break
                continue
            if STOP_LABELS.match(nxt):
                break
            # A new obvious heading is more likely a footer/section than subject text.
            if re.match(r"^(?:सेवा में|महोदय|मान्यवर|प्रतिलिपि|नोट|आदेश)\b", nxt):
                break
            parts.append(nxt)
            if len(" ".join(parts)) >= max_chars:
                break
        value = re.sub(r"\s+", " ", " ".join(parts)).strip()
        if value:
            return value[:max_chars]
    return None
