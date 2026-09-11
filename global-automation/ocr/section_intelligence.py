"""Conservative section, annexure and attachment boundary intelligence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable

from .document_structure import StructureBlock


@dataclass(frozen=True)
class SectionBoundary:
    boundary_id: str
    page_number: int
    block_id: str
    boundary_type: str
    label: str
    confidence: float


_SECTION_PATTERNS = (
    ("annexure", re.compile(r"\b(?:annexure|annex|परिशिष्ट|अनुलग्नक)\b", re.I)),
    ("attachment", re.compile(r"\b(?:attachment|enclosure|संलग्नक)\b", re.I)),
    ("section", re.compile(r"^(?:section|भाग|खंड|विषय|subject)\b", re.I)),
)


def detect_section_boundaries(blocks: Iterable[StructureBlock]) -> tuple[SectionBoundary, ...]:
    """Detect explicit textual boundary markers without inventing structure."""
    result: list[SectionBoundary] = []
    for block in sorted(blocks, key=lambda b: (b.page_number, b.y, b.x, b.block_id)):
        text = " ".join(block.text.split()).strip()
        if not text:
            continue
        for boundary_type, pattern in _SECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                confidence = round(min(0.95, 0.55 + (0.15 if block.block_type == "heading_or_label" else 0.0) + min(0.20, block.confidence * 0.20)), 2)
                result.append(SectionBoundary(
                    boundary_id=f"{block.block_id}-{boundary_type}",
                    page_number=block.page_number,
                    block_id=block.block_id,
                    boundary_type=boundary_type,
                    label=match.group(0),
                    confidence=confidence,
                ))
                break
    return tuple(result)


def section_boundaries_to_dict(boundaries: Iterable[SectionBoundary]) -> list[dict]:
    return [asdict(item) for item in boundaries]


__all__ = ["SectionBoundary", "detect_section_boundaries", "section_boundaries_to_dict"]
