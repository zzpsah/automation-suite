"""Capability matrix and deterministic self-test for Global Sarkari OCR.

This is an engineering capability test, not a claim of accuracy on unseen
production documents. It exercises the public document-intelligence contract
without requiring a real PDF or external service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .government_document import analyze_document


@dataclass(frozen=True)
class Capability:
    name: str
    status: str
    evidence: str


SAMPLE = """बिहार विद्यालय परीक्षा समिति
विज्ञप्ति संख्या पी०आर० 173/2026
दिनांक: 05.08.2026
विषय: सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में

1. राज्य के इण्टरस्तरीय शिक्षण संस्थानों को सूचित किया जाता है।
2. स्पॉट नामांकन की तिथि दिनांक 15.09.2026 से 18.09.2026 तक अंतिम रूप से विस्तारित की जाती है।
"""


def run_self_test() -> dict[str, object]:
    result = analyze_document(SAMPLE)
    checks: dict[str, bool] = {
        "header_authority": result["authority"]["value"] == "बिहार विद्यालय परीक्षा समिति",
        "official_subject": bool(result["subject"]["value"] and "स्पॉट नामांकन" in result["subject"]["value"]),
        "classification": result["document_type"]["value"] == "admission",
        "deadline_extraction": "18.09.2026" in result["deadlines"],
        "short_description": bool(result["short_description"]),
        "evidence_policy": result["evidence_policy"] == "source-backed; no invented metadata",
    }
    return {"passed": all(checks.values()), "checks": checks}


def capability_matrix() -> list[Capability]:
    return [
        Capability("PDF embedded-text extraction", "implemented", "ocr_engine / service"),
        Capability("Rendered Hindi+English OCR", "implemented", "Tesseract backend"),
        Capability("OCR correction", "implemented", "correction layer"),
        Capability("Sarkari normalization", "implemented", "sarkari_normalizer"),
        Capability("Bihar authority/office resolution", "implemented", "Bihar language pack + resolver"),
        Capability("Header-first issuing authority", "implemented", "government_document"),
        Capability("Official multiline subject", "implemented", "government_document"),
        Capability("Government document classification", "implemented", "government_document"),
        Capability("Action extraction", "implemented", "government_document"),
        Capability("Deadline extraction", "implemented", "government_document"),
        Capability("Evidence-backed short description", "implemented", "government_document"),
        Capability("Field confidence", "implemented", "ocr_service"),
        Capability("Regression corpus / promotion workflow", "implemented", "training + tests"),
        Capability("General Indian government coverage", "limited", "requires reviewed language/office packs"),
        Capability("ML/VLM fine-tuned government understanding", "not yet", "future model backend"),
    ]
