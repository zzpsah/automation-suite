"""Dependency-free structured observability primitives."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import time
from typing import Mapping


@dataclass(frozen=True)
class OperationEvent:
    operation: str
    status: str
    duration_ms: float
    fields: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"operation": self.operation, "status": self.status,
                "duration_ms": round(self.duration_ms, 3), "fields": dict(self.fields)}


def emit_event(operation: str, status: str, *, started_at: float | None = None,
               fields: Mapping[str, object] | None = None) -> OperationEvent:
    """Create a JSON-safe event without logging sensitive source document content."""
    duration_ms = 0.0 if started_at is None else max(0.0, (time.monotonic() - started_at) * 1000)
    return OperationEvent(operation, status, duration_ms, fields or {})


def event_to_json(event: OperationEvent) -> str:
    return json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)


__all__ = ["OperationEvent", "emit_event", "event_to_json"]
