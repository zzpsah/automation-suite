import json

from ocr.document_understanding import DocumentUnderstandingGraph, UnderstandingEntity
from ocr.reference_timeline import build_reference_timeline, reference_timeline_to_dict


def entity(entity_id, kind, value, page=1, block="b1", confidence=0.9):
    return UnderstandingEntity(entity_id, kind, value, page, block, confidence)


def graph(*entities):
    return DocumentUnderstandingGraph(tuple(entities), ())


def test_timeline_sorts_explicit_dates_and_attaches_same_block_reference():
    result = build_reference_timeline({
        "doc-b": graph(
            entity("r2", "reference", "REF-2", 1, "b1"),
            entity("d2", "date", "12/09/2026", 1, "b1", 0.86),
        ),
        "doc-a": graph(
            entity("r1", "reference", "REF-1", 1, "b1"),
            entity("d1", "date", "01/09/2026", 1, "b1", 0.86),
        ),
    })
    assert [event.document_id for event in result.events] == ["doc-a", "doc-b"]
    assert result.events[0].date_iso == "2026-09-01"
    assert result.events[0].reference_entity_ids == ("r1",)


def test_unparseable_date_is_retained_after_dated_events():
    result = build_reference_timeline({
        "a": graph(entity("d1", "date", "not-a-date")),
        "b": graph(entity("d2", "date", "02/09/2026")),
    })
    assert [event.document_id for event in result.events] == ["b", "a"]
    assert result.events[-1].date_iso is None


def test_document_filter_and_json_serialization():
    timeline = build_reference_timeline({
        "a": graph(entity("d1", "date", "02/09/2026")),
        "b": graph(entity("d2", "date", "03/09/2026")),
    }, ("b",))
    payload = reference_timeline_to_dict(timeline)
    assert [event["document_id"] for event in payload["events"]] == ["b"]
    assert isinstance(payload["events"][0]["reference_entity_ids"], list)
    json.dumps(payload)
