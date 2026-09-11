"""Evidence-preserving document/reference timeline intelligence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
import re
from typing import Mapping

from .document_understanding import DocumentUnderstandingGraph, UnderstandingEntity


@dataclass(frozen=True)
class TimelineEvent:
    document_id: str
    event_type: str
    date_text: str
    date_iso: str | None
    page_number: int
    block_id: str
    date_entity_id: str
    reference_entity_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class ReferenceTimeline:
    events: tuple[TimelineEvent, ...]


_NUMERIC_DATE_RE = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$")
_MONTH_DATE_RE = re.compile(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", re.I)
_MONTHS = {name.lower(): index for index, name in enumerate((
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
), 1)}


def _parse_date(value: str) -> date | None:
    text = value.strip()
    match = _NUMERIC_DATE_RE.fullmatch(text)
    if match:
        day, month, year = (int(part) for part in match.groups())
        if year < 100:
            year += 2000 if year < 70 else 1900
        try:
            return date(year, month, day)
        except ValueError:
            return None
    match = _MONTH_DATE_RE.fullmatch(text)
    if match:
        day, month_name, year = match.groups()
        month = _MONTHS.get(month_name.lower())
        if month is None:
            return None
        try:
            return date(int(year), month, int(day))
        except ValueError:
            return None
    return None


def _event_key(event: TimelineEvent) -> tuple:
    return (
        event.date_iso is None,
        event.date_iso or "9999-12-31",
        event.document_id,
        event.page_number,
        event.block_id,
        event.date_entity_id,
    )


def build_reference_timeline(
    documents: Mapping[str, DocumentUnderstandingGraph],
    document_ids: tuple[str, ...] | None = None,
) -> ReferenceTimeline:
    """Build a chronological view of explicitly extracted document dates.

    A date is represented only as a source-level date entity. References found in
    the same source block are attached as evidence; no legal event meaning is
    invented. Documents without parseable dates are retained after dated events.
    """
    selected = set(document_ids) if document_ids is not None else None
    events: list[TimelineEvent] = []
    for raw_document_id, graph in sorted(documents.items(), key=lambda item: str(item[0])):
        document_id = str(raw_document_id)
        if selected is not None and document_id not in selected:
            continue
        by_block: dict[str, list[UnderstandingEntity]] = {}
        for entity in graph.entities:
            by_block.setdefault(entity.block_id, []).append(entity)
        for entity in graph.entities:
            if entity.entity_type != "date":
                continue
            parsed = _parse_date(entity.value)
            references = tuple(sorted(
                e.entity_id for e in by_block.get(entity.block_id, ())
                if e.entity_type == "reference"
            ))
            events.append(TimelineEvent(
                document_id=document_id,
                event_type="document_date",
                date_text=entity.value,
                date_iso=parsed.isoformat() if parsed else None,
                page_number=entity.page_number,
                block_id=entity.block_id,
                date_entity_id=entity.entity_id,
                reference_entity_ids=references,
                confidence=entity.confidence,
            ))
    events.sort(key=_event_key)
    return ReferenceTimeline(tuple(events))


def reference_timeline_to_dict(timeline: ReferenceTimeline) -> dict:
    payload = []
    for event in timeline.events:
        item = asdict(event)
        item["reference_entity_ids"] = list(event.reference_entity_ids)
        payload.append(item)
    return {"events": payload}


__all__ = ["TimelineEvent", "ReferenceTimeline", "build_reference_timeline", "reference_timeline_to_dict"]
