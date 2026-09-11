"""Privacy-safe line-level OCR disagreement analysis."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from .backend import OCRResult


@dataclass(frozen=True)
class LineDisagreement:
    line_number: int
    texts: tuple[str, ...]
    backends: tuple[str, ...]
    similarity: float
    disagreement: bool


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def compare_lines(results: Iterable[OCRResult]) -> tuple[LineDisagreement, ...]:
    """Compare corresponding non-empty lines while preserving no source image data."""
    items = list(results)
    if not items:
        raise ValueError("No OCR results supplied")
    split = [_lines(item.text) for item in items]
    count = max((len(lines) for lines in split), default=0)
    output: list[LineDisagreement] = []
    for index in range(count):
        entries = [(item.backend, lines[index] if index < len(lines) else "") for item, lines in zip(items, split)]
        texts = tuple(text for _, text in entries)
        nonempty = [text for text in texts if text]
        if len(nonempty) < 2:
            similarity = 1.0
        else:
            pairs = [SequenceMatcher(None, nonempty[0], text).ratio() for text in nonempty[1:]]
            similarity = sum(pairs) / len(pairs)
        output.append(LineDisagreement(
            line_number=index + 1,
            texts=texts,
            backends=tuple(backend for backend, _ in entries),
            similarity=round(similarity, 4),
            disagreement=len(set(nonempty)) > 1,
        ))
    return tuple(output)


__all__ = ["LineDisagreement", "compare_lines"]
