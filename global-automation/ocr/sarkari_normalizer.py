"""Reusable Hindi/English government-document OCR normalization helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

LABELS = {
    "subject": ["विषय", "विषयक", "subject", "sub."],
    "reference_number": ["पत्रांक", "ज्ञापांक", "पत्र संख्या", "पत्र सं.", "पत्र सं", "क्रमांक", "reference no", "reference number", "memo no", "memo number"],
    "issue_date": ["दिनांक", "दिनांकित", "date", "dated"],
    "authority": ["प्रेषक", "जारीकर्ता", "जारी करने वाला कार्यालय", "प्रेषित", "issuing authority", "issued by", "from", "sender"],
    "office": ["कार्यालय", "office"],
    "department": ["विभाग", "department"],
}

KNOWN_AUTHORITIES = [
    "बिहार विद्यालय परीक्षा समिति", "शिक्षा विभाग, बिहार", "शिक्षा विभाग",
    "बिहार शिक्षा परियोजना परिषद", "बिहार शिक्षा परियोजना परिषद्",
    "जिला शिक्षा पदाधिकारी", "प्रखंड शिक्षा पदाधिकारी",
    "District Education Officer", "Block Education Officer",
    "Bihar School Examination Board", "BSEB",
]

AUTHORITY_CANONICAL = {
    "बिहार शिक्षा परियोजना परिषद्": "बिहार शिक्षा परियोजना परिषद",
    "Bihar School Examination Board": "बिहार विद्यालय परीक्षा समिति",
    "BSEB": "बिहार विद्यालय परीक्षा समिति",
}

@dataclass
class SarkariMetadata:
    subject: Optional[str] = None
    authority: Optional[str] = None
    reference_number: Optional[str] = None
    issue_date: Optional[str] = None
    office: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None
    confidence: str = "LOW"
    def to_dict(self): return asdict(self)

def clean_line(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" :-–—|\t")

def normalize_sarkari_text(text: str) -> str:
    text = (text or "").replace("\u00a0", " ").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_labeled_line(text: str, labels: list[str], max_len: int = 1000) -> Optional[str]:
    for raw in text.splitlines():
        line = clean_line(raw)
        if not line: continue
        lower = line.lower()
        for label in labels:
            lc = label.lower().rstrip(".")
            if lower.startswith(lc + ":") or lower.startswith(lc + " -") or lower.startswith(lc + " "):
                value = re.sub(r"^\s*[^:–—-]{1,80}\s*[:–—-]\s*", "", line, count=1)
                if value == line: value = line[len(label):].strip(" :-–—")
                value = clean_line(value)
                if value and len(value) <= max_len: return value
    return None

def normalize_authority(value: Optional[str]) -> Optional[str]:
    if not value: return None
    cleaned = clean_line(value)
    for alias, canonical in AUTHORITY_CANONICAL.items():
        if cleaned.lower() == alias.lower(): return canonical
    return cleaned

def find_known_authority(text: str) -> Optional[str]:
    lower = text.lower()
    # Prefer specific/full names over short aliases.
    for authority in sorted(KNOWN_AUTHORITIES, key=len, reverse=True):
        if authority.lower() in lower:
            return normalize_authority(authority)
    return None

def normalize_issue_date(value: Optional[str]) -> Optional[str]:
    if not value: return None
    value = clean_line(value)
    match = re.search(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{4})(?!\d)", value)
    if not match: return value
    day, month, year = map(int, match.groups())
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return value

def classify_document(text: str) -> Optional[str]:
    t = text.lower()
    if re.search(r"स्पॉट नामांकन|spot admission|ofss|नामांकन|admission", t): return "admission"
    if re.search(r"परीक्षा|exam|परीक्षार्थी|result|परिणाम", t): return "examination"
    if re.search(r"बिहार विद्यालय परीक्षा समिति|bseb|board examination", t): return "bseb"
    if re.search(r"छात्र|student|विद्यार्थी", t): return "student"
    if re.search(r"शिक्षक|teacher|staff", t): return "staff"
    return "other"

def extract_metadata(text: str) -> SarkariMetadata:
    source = normalize_sarkari_text(text)
    md = SarkariMetadata()
    md.subject = extract_labeled_line(source, LABELS["subject"], 1000)
    md.reference_number = extract_labeled_line(source, LABELS["reference_number"], 250)
    md.issue_date = normalize_issue_date(extract_labeled_line(source, LABELS["issue_date"], 100))
    md.authority = find_known_authority(source) or normalize_authority(extract_labeled_line(source, LABELS["authority"], 300))
    md.office = extract_labeled_line(source, LABELS["office"], 300)
    md.department = extract_labeled_line(source, LABELS["department"], 300)
    md.category = classify_document(source)
    score = sum(bool(x) for x in [md.subject, md.authority, md.reference_number, md.issue_date])
    md.confidence = "HIGH" if score >= 3 else "MEDIUM" if score >= 1 else "LOW"
    return md
