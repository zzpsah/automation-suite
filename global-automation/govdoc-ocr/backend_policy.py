"""Explainable, conservative backend selection for GovDOC Vision."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BackendDecision:
    backend: str
    reason: str
    escalated: bool = False

def choose_backend(*, requested: str = "tesseract", quality_score: float | None = None,
                   available: tuple[str, ...] = ("tesseract",), threshold: float = 0.35) -> BackendDecision:
    if requested not in available:
        raise ValueError(f"Requested backend is unavailable: {requested}")
    if quality_score is not None and not 0 <= quality_score <= 1:
        raise ValueError("quality_score must be between 0 and 1")
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if quality_score is not None and quality_score < threshold and "paddleocr" in available and requested == "tesseract":
        return BackendDecision("paddleocr", "low image quality; optional backend escalation", True)
    return BackendDecision(requested, "explicit/default backend policy")
