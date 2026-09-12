"""Conservative Hindi/English government-document normalization.

The normalizer is intentionally evidence-safe: it may repair formatting,
Unicode variants, known OCR vocabulary aliases, and high-confidence
administrative phrasing, but it never invents missing facts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LABEL_ALIASES = {
    "विषयक": "विषय:", "विषयः": "विषय:", "पत्र संख्या": "पत्रांक:",
    "पत्र सं.": "पत्रांक:", "पत्र सं": "पत्रांक:", "ज्ञाप संख्या": "ज्ञापांक:",
    "ज्ञाप सं.": "ज्ञापांक:", "दिनांकित": "दिनांक:", "दिनांकः": "दिनांक:",
    "संदर्भः": "संदर्भ:", "सेवामें": "सेवा में:",
}

PHRASE_ALIASES = {
    "के संबंध मे": "के संबंध में", "के सम्बन्ध मे": "के संबंध में",
    "के सम्बन्ध में": "के संबंध में", "के संबंधी में": "के संबंध में",
    "आवश्यक कार्यवाही": "आवश्यक कार्रवाई",
    "अग्रसारित किया जाता है": "अग्रेषित किया जाता है",
    "उपरोक्त विषयक": "उपरोक्त विषय के संबंध में",
}

UNICODE_EQUIVALENTS = {"ड़": "ड़", "ढ़": "ढ़", "क़": "क", "फ़": "फ", "ज़": "ज", "ऱ": "र"}


def _load_ocr_aliases() -> dict[str, str]:
    """Load canonical Bihar education aliases when the language pack is present."""
    pack = Path(__file__).resolve().parent / "language_packs" / "bihar_education.json"
    try:
        data = json.loads(pack.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    mapping: dict[str, str] = {}
    for canonical, variants in data.get("ocr_aliases", {}).items():
        for variant in variants:
            if variant != canonical:
                mapping[variant] = canonical
    return mapping


def normalize_unicode(text: str) -> str:
    for src, dst in UNICODE_EQUIVALENTS.items():
        text = text.replace(src, dst)
    return text


def normalize_whitespace(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")).strip()


def normalize_ocr_aliases(text: str) -> str:
    for src, dst in sorted(_load_ocr_aliases().items(), key=lambda item: -len(item[0])):
        text = text.replace(src, dst)
    return text


def normalize_labels(text: str) -> str:
    for src, dst in sorted(LABEL_ALIASES.items(), key=lambda item: -len(item[0])):
        text = text.replace(src, dst)
    return text


def normalize_phrases(text: str) -> str:
    for src, dst in sorted(PHRASE_ALIASES.items(), key=lambda item: -len(item[0])):
        text = text.replace(src, dst)
    return text


def normalize_dates(text: str) -> str:
    return re.sub(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})(?!\d)", r"\1/\2/\3", text)


def normalize_punctuation(text: str) -> str:
    text = text.replace("।", ".").replace("ः", ":").replace("–", "-").replace("—", "-")
    text = re.sub(r"[ \t]+([,.:;])", r"\1", text)
    text = re.sub(r"([,;:]){2,}", r"\1", text)
    return text


def normalize_sarkari_text(text: str) -> str:
    """Return conservative, reproducible administrative-language normalization."""
    value = normalize_whitespace(text)
    value = normalize_unicode(value)
    value = normalize_ocr_aliases(value)
    value = normalize_labels(value)
    value = normalize_phrases(value)
    value = normalize_dates(value)
    value = normalize_punctuation(value)
    return normalize_whitespace(value)
