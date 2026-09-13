"""Evidence-based structure extraction for Indian government letters.

This layer sits after OCR/normalization. It does not invent metadata: every
field is either directly supported by text evidence or left empty.
"""
from __future__ import annotations

import re
from typing import Any


_AUTHORITY_HINTS = (
    "बिहार विद्यालय परीक्षा समिति", "शिक्षा विभाग", "बिहार शिक्षा परियोजना परिषद",
    "जिला शिक्षा पदाधिकारी", "प्रखंड शिक्षा पदाधिकारी", "जिला कार्यक्रम पदाधिकारी",
    "राज्य परियोजना निदेशक", "निदेशक, माध्यमिक शिक्षा", "निदेशक, प्राथमिक शिक्षा",
    "Bihar School Examination Board", "BSEB", "District Education Officer",
    "Block Education Officer",
)

_TYPE_RULES = [
    ("admission", ("स्पॉट नामांकन", "नामांकन", "OFSS", "spot admission", "admission")),
    ("examination", ("परीक्षा", "परीक्षार्थी", "परीक्षा कार्यक्रम", "result", "परिणाम", "exam")),
    ("transfer", ("स्थानांतरण", "स्थानान्तरण", "पदस्थापन", "transfer")),
    ("service", ("सेवा इतिहास", "सेवा संबंधी", "सेवाकाल", "service")),
    ("training", ("प्रशिक्षण", "training")),
    ("scholarship", ("छात्रवृत्ति", "scholarship")),
    ("holiday", ("अवकाश", "holiday")),
]

_ACTION_PATTERNS = (
    r"(?:तिथि|दिनांक)\s+(?:को|तक)?\s*(?:विस्तारित|निर्धारित|निश्चित)",
    r"(?:अंतिम रूप से|तक)\s+(?:विस्तारित|निर्धारित)",
    r"(?:सूचित|निर्देशित|अनुरोध|अपील|आदेश)\s+(?:किया|करते|दिया|गया)",
    r"(?:करना|करें|कराया|लेने|जमा करने|प्रदर्शित करने)\s+(?:होगा|होगी|करेंगे|करें)",
)


def _lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", x).strip() for x in (text or "").splitlines() if x.strip()]


def _header(lines: list[str], ratio: float = 0.22) -> list[str]:
    return lines[: max(8, int(len(lines) * ratio))]


def _contains(line: str, terms: tuple[str, ...]) -> bool:
    low = line.casefold()
    return any(term.casefold() in low for term in terms)


def extract_header_authority(text: str) -> dict[str, Any]:
    """Resolve authority from the header before considering body references."""
    lines = _lines(text)
    candidates: list[tuple[int, str]] = []
    for idx, line in enumerate(_header(lines)):
        if _contains(line, _AUTHORITY_HINTS):
            candidates.append((idx, line))
    if not candidates:
        return {"value": None, "source": None, "confidence": "LOW"}
    # Prefer a line that is itself an authority, then the earliest header hit.
    exact = [x for x in candidates if any(x[1].casefold().strip(" :-") == a.casefold() for a in _AUTHORITY_HINTS)]
    value = (exact[0] if exact else candidates[0])[1]
    return {"value": value[:300], "source": "header", "confidence": "HIGH"}


def extract_official_subject(text: str, fallback: str | None = None) -> dict[str, Any]:
    """Extract the subject line while avoiding body paragraph contamination."""
    lines = _lines(text)
    label = re.compile(r"^\s*(?:विषय|विषयक|subject)\s*[:：\-–—]?\s*(.*)$", re.I)
    stops = re.compile(r"^(?:पत्रांक|ज्ञापांक|क्रमांक|दिनांक|कार्यालय|विभाग|सेवा में|महोदय|प्रतिलिपि|प्रति|संलग्न)\b", re.I)
    for i, line in enumerate(lines):
        m = label.match(line)
        if not m:
            continue
        parts = [m.group(1).strip(" :-–—")] if m.group(1).strip() else []
        for nxt in lines[i + 1 : i + 4]:
            if stops.match(nxt):
                break
            # Stop when a clearly numbered body paragraph starts.
            if re.match(r"^\s*\d+[.)]\s+", nxt):
                break
            parts.append(nxt)
        value = re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()
        if 8 <= len(value) <= 500:
            return {"value": value, "source": "subject_label", "confidence": "HIGH"}
    if fallback and 8 <= len(fallback.strip()) <= 500:
        return {"value": fallback.strip(), "source": "normalized_subject", "confidence": "MEDIUM"}
    return {"value": None, "source": None, "confidence": "LOW"}


def classify_document(text: str) -> dict[str, Any]:
    low = (text or "").casefold()
    scores = {key: sum(1 for term in terms if term.casefold() in low) for key, terms in _TYPE_RULES}
    best = max(scores, key=scores.get) if scores else "other"
    score = scores.get(best, 0)
    return {"value": best if score else "other", "evidence_terms": [k for k, v in scores.items() if v], "confidence": "HIGH" if score >= 2 else "MEDIUM" if score else "LOW"}


def extract_actions(text: str) -> list[str]:
    lines = _lines(text)
    hits: list[str] = []
    for line in lines:
        if any(re.search(p, line, re.I) for p in _ACTION_PATTERNS):
            hits.append(line[:500])
    return hits[:5]


def extract_deadlines(text: str) -> list[str]:
    # Preserve source date wording; normalization belongs to the existing date layer.
    patterns = (
        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",
        r"दिनांक\s+\d{1,2}[./-]\d{1,2}[./-]\d{4}",
    )
    hits: list[str] = []
    for p in patterns:
        hits.extend(re.findall(p, text or "", flags=re.I))
    return list(dict.fromkeys(hits))[:12]


def build_short_description(subject: str | None, actions: list[str], category: str | None) -> str | None:
    """Produce a compact description only from extracted evidence."""
    if not subject:
        return None
    action = actions[0] if actions else None
    if action:
        return f"{subject.rstrip('.')}। पत्र में संबंधित कार्यवाही/निर्देश के रूप में {action[:220]}।"
    if category:
        return f"यह दस्तावेज़ {category} संबंधी सूचना/निर्देश से संबंधित है: {subject.rstrip('.')}."
    return subject.rstrip(".") + "।"


def analyze_document(text: str, normalized_subject: str | None = None) -> dict[str, Any]:
    """Return structured government-document intelligence with evidence metadata."""
    authority = extract_header_authority(text)
    subject = extract_official_subject(text, normalized_subject)
    classification = classify_document(text)
    actions = extract_actions(text)
    deadlines = extract_deadlines(text)
    summary = build_short_description(subject["value"], actions, classification["value"])
    return {
        "authority": authority,
        "subject": subject,
        "document_type": classification,
        "actions": actions,
        "deadlines": deadlines,
        "short_description": summary,
        "evidence_policy": "source-backed; no invented metadata",
    }
