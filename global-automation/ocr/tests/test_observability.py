import json

from ocr.observability import OperationEvent, emit_event, event_to_json


def test_event_is_json_safe_and_excludes_source_content() -> None:
    event = OperationEvent("ocr.process", "ok", 12.345, {"pages": 2, "backend": "tesseract"})
    payload = json.loads(event_to_json(event))
    assert payload["operation"] == "ocr.process"
    assert payload["status"] == "ok"
    assert payload["duration_ms"] == 12.345
    assert "text" not in payload


def test_emit_event_duration_is_non_negative() -> None:
    event = emit_event("search", "ok")
    assert event.duration_ms == 0.0
