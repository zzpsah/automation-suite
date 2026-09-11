"""Multi-page document structure intelligence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PageStructure:
    page_number: int
    text: str
    repeated_header: bool = False
    repeated_footer: bool = False
    continuation: bool = False


def _normalized_line(line: str) -> str:
    return " ".join(line.split()).casefold()


def analyze_pages(pages: Iterable[str], *, repeated_threshold: float = 0.6) -> dict:
    """Detect repeated headers/footers and likely page continuations.

    This is intentionally text-structural. It does not infer missing content.
    """
    page_list = [str(p or "") for p in pages]
    if not page_list:
        return {"page_count": 0, "pages": [], "repeated_headers": [], "repeated_footers": []}
    threshold = float(repeated_threshold)
    if not 0.0 < threshold <= 1.0:
        raise ValueError("repeated_threshold must be in (0, 1]")

    top_counts: dict[str, int] = {}
    bottom_counts: dict[str, int] = {}
    top_lines: list[str] = []
    bottom_lines: list[str] = []
    for text in page_list:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        top = _normalized_line(lines[0]) if lines else ""
        bottom = _normalized_line(lines[-1]) if lines else ""
        top_lines.append(top)
        bottom_lines.append(bottom)
        if top:
            top_counts[top] = top_counts.get(top, 0) + 1
        if bottom:
            bottom_counts[bottom] = bottom_counts.get(bottom, 0) + 1

    minimum = max(2, int(len(page_list) * threshold + 0.999)) if len(page_list) > 1 else 2
    repeated_headers = {k for k, v in top_counts.items() if v >= minimum}
    repeated_footers = {k for k, v in bottom_counts.items() if v >= minimum}

    structures: list[PageStructure] = []
    for index, text in enumerate(page_list, 1):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        top = _normalized_line(lines[0]) if lines else ""
        bottom = _normalized_line(lines[-1]) if lines else ""
        continuation = False
        if index > 1 and lines and page_list[index - 2].rstrip().endswith(("-", "…", ",", ":")):
            continuation = True
        structures.append(PageStructure(index, text, top in repeated_headers, bottom in repeated_footers, continuation))

    return {
        "page_count": len(page_list),
        "repeated_headers": sorted(repeated_headers),
        "repeated_footers": sorted(repeated_footers),
        "pages": [s.__dict__ for s in structures],
    }


__all__ = ["PageStructure", "analyze_pages"]
