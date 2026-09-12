"""Small, storage-neutral provenance records for OCR-derived evidence."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceRef:
    source: str
    page: int | None = None
    region_id: str | None = None
    field: str | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in {"source": self.source, "page": self.page, "region_id": self.region_id, "field": self.field}.items() if v is not None}


def field_evidence(*, source: str, page: int | None = None, region_id: str | None = None, field: str | None = None) -> dict:
    """Create an explicit evidence pointer; callers remain responsible for storage."""
    return EvidenceRef(source, page, region_id, field).to_dict()
