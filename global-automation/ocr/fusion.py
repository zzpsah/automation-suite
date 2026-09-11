"""Deterministic multi-backend OCR consensus utilities."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .backend import OCRResult


@dataclass(frozen=True)
class ConsensusResult:
    text: str
    confidence: float | None
    agreeing_backends: tuple[str, ...]
    disagreement: bool


def _line_vote(results: list[OCRResult]) -> tuple[str, tuple[str, ...], bool]:
    lines = [result.text.strip() for result in results if result.text.strip()]
    if not lines:
        return "", (), False
    counts = Counter(lines)
    winner, votes = min(counts.items(), key=lambda item: (-item[1], item[0]))
    agreeing = tuple(sorted(result.backend for result in results if result.text.strip() == winner))
    return winner, agreeing, len(counts) > 1


def consensus(results: Iterable[OCRResult]) -> ConsensusResult:
    """Build a conservative consensus from backend outputs.

    Consensus is only an OCR-quality signal. It never edits source evidence or
    silently substitutes a result when backends disagree.
    """
    items = list(results)
    if not items:
        raise ValueError("No OCR results supplied")
    text, agreeing, disagreement = _line_vote(items)
    scores = [r.confidence for r in items if r.text.strip() == text and r.confidence is not None]
    confidence = sum(scores) / len(scores) if scores else None
    return ConsensusResult(
        text=text,
        confidence=confidence,
        agreeing_backends=agreeing,
        disagreement=disagreement,
    )


__all__ = ["ConsensusResult", "consensus"]
