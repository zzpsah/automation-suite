"""Conservative, project-agnostic OCR correction helpers.

The correction layer intentionally runs before semantic metadata extraction and
never rewrites the evidence stored by consumers.  Rules are conservative and
focused on common Hindi government-document OCR artefacts.
"""
from __future__ import annotations

import re

# Labels commonly fragmented by OCR. Values are canonical spellings.
_LABEL_ALIASES = {
    "विषयक": "विषय",
    "विषय :": "विषय:",
    "विषय-": "विषय:",
    "पत्र संख्या": "पत्रांक",
    "पत्र सं०": "पत्रांक",
    "पत्र सं.": "पत्रांक",
    "पत्र सं": "पत्रांक",
    "ज्ञाप संख्या": "ज्ञापांक",
    "ज्ञाप सं०": "ज्ञापांक",
    "ज्ञाप सं.": "ज्ञापांक",
    "दिनांकित": "दिनांक",
    "दिनांक :": "दिनांक:",
    "दिनांक-": "दिनांक:",
}

# OCR frequently emits these whitespace variants around administrative labels.
_LABEL_RE = re.compile(
    r"(?m)^\\s*(विषयक|विषय|पत्र\\s*सं(?:ख्या|[०o.]*)?|ज्ञाप\\s*सं(?:ख्या|[०o.]*)?|दिनांकित|दिनांक)\\s*[:：\\-]?\\s*"
)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving line boundaries and evidence order."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def normalize_labels(text: str) -> str:
    """Canonicalize common Hindi/English administrative labels conservatively."""
    for source, target in sorted(_LABEL_ALIASES.items(), key=lambda item: -len(item[0])):
        text = text.replace(source, target)
    return _LABEL_RE.sub(lambda m: {"विषयक": "विषय:", "विषय": "विषय:", "पत्र सं": "पत्रांक:", "ज्ञाप सं": "ज्ञापांक:", "दिनांकित": "दिनांक:", "दिनांक": "दिनांक:"}.get(m.group(1), m.group(0)), text)


def normalize_dates(text: str) -> str:
    """Standardize separator spacing for numeric dates without changing values."""
    return re.sub(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})(?!\d)", r"\1/\2/\3", text)


def correct_ocr_text(text: str) -> str:
    """Apply safe OCR corrections suitable for any government-document project."""
    if not text:
        return ""
    text = normalize_whitespace(text)
    text = normalize_labels(text)
    text = normalize_dates(text)
    return normalize_whitespace(text)
