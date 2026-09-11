"""Unicode-safe OCR accuracy metrics for benchmark evaluation.

These metrics evaluate OCR output against reviewed ground truth. They are kept
separate from image-quality metrics so preprocessing gains can be measured
without conflating visual diagnostics with transcription accuracy.
"""
from __future__ import annotations

import re
from typing import Sequence

_WHITESPACE = re.compile(r"\s+")


def normalize_for_eval(text: str) -> str:
    """Normalize only whitespace for fair OCR comparison.

    Source wording, Devanagari characters, punctuation and numbers are otherwise
    preserved. This is intentionally not the production Sarkari normalizer.
    """
    return _WHITESPACE.sub(" ", text.strip())


def _edit_distance(left: Sequence[str], right: Sequence[str]) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, left_item in enumerate(left, 1):
        current = [i]
        for j, right_item in enumerate(right, 1):
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (left_item != right_item),
            ))
        previous = current
    return previous[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Return character error rate (0 is perfect)."""
    ref = list(normalize_for_eval(reference))
    hyp = list(normalize_for_eval(hypothesis))
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def wer(reference: str, hypothesis: str) -> float:
    """Return word error rate (0 is perfect)."""
    ref = normalize_for_eval(reference).split(" ") if normalize_for_eval(reference) else []
    hyp = normalize_for_eval(hypothesis).split(" ") if normalize_for_eval(hypothesis) else []
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def accuracy_report(reference: str, hypothesis: str) -> dict[str, float | int]:
    """Return deterministic CER/WER plus reference sizes."""
    normalized_reference = normalize_for_eval(reference)
    return {
        "cer": round(cer(reference, hypothesis), 6),
        "wer": round(wer(reference, hypothesis), 6),
        "reference_characters": len(normalized_reference),
        "reference_words": len(normalized_reference.split()) if normalized_reference else 0,
    }
