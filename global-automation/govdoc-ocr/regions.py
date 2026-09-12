"""Normalized OCR region contract for GovDOC Vision.

Coordinates are pixel-space [x1, y1, x2, y2]. Backends may return no regions;
empty is preferred to fabricated geometry.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class OCRRegion:
    id: str
    bbox: tuple[int, int, int, int]
    text: str
    confidence: float | None = None
    block_type: str | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["bbox"] = list(self.bbox)
        return value

def normalize_region(region: OCRRegion | dict[str, Any], index: int = 1) -> OCRRegion:
    if isinstance(region, OCRRegion):
        return region
    bbox = tuple(int(round(float(v))) for v in region.get("bbox", []))
    if len(bbox) != 4:
        raise ValueError("OCR region bbox must contain four coordinates")
    x1, y1, x2, y2 = bbox
    if x2 < x1 or y2 < y1:
        raise ValueError("OCR region bbox must be ordered x1,y1,x2,y2")
    return OCRRegion(
        id=str(region.get("id") or f"region-{index}"), bbox=bbox,
        text=str(region.get("text") or ""),
        confidence=region.get("confidence"), block_type=region.get("block_type"),
        source=region.get("source"),
    )

def regions_to_dict(regions: list[OCRRegion | dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_region(r, i).to_dict() for i, r in enumerate(regions, 1)]
