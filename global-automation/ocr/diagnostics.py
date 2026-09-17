"""Privacy-safe diagnostics for OCR pages.

Diagnostics contain measurements only. They intentionally do not store or log
page text, filenames, document identifiers, or source content.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PageOCRDiagnostic:
    page_number: int
    output_characters: int
    non_whitespace_characters: int
    line_count: int
    blank: bool
    likely_weak: bool


def diagnose_page_text(page_number: int, text: str, *, weak_char_threshold: int = 20) -> PageOCRDiagnostic:
    """Measure OCR output quality for one page without retaining its content."""
    if page_number < 1:
        raise ValueError("page_number must be >= 1")
    value = text or ""
    non_whitespace = len("".join(value.split()))
    lines = [line for line in value.splitlines() if line.strip()]
    return PageOCRDiagnostic(
        page_number=page_number,
        output_characters=len(value),
        non_whitespace_characters=non_whitespace,
        line_count=len(lines),
        blank=non_whitespace == 0,
        likely_weak=non_whitespace < weak_char_threshold,
    )


def diagnose_pages(page_texts: list[str], *, weak_char_threshold: int = 20) -> list[dict[str, object]]:
    """Return deterministic diagnostics for an ordered list of page outputs."""
    return [asdict(diagnose_page_text(i, text, weak_char_threshold=weak_char_threshold)) for i, text in enumerate(page_texts, 1)]
