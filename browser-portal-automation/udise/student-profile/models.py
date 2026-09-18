from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


PROFILE_TYPES = ("general", "education", "facility")


@dataclass
class FieldObservation:
    key: str
    label: str
    portal_value: Any = None
    section: str | None = None
    control_type: str | None = None
    editable: bool | None = None
    required: bool | None = None
    locator: dict[str, str] | None = None
    notes: str | None = None


@dataclass
class ProfileSnapshot:
    profile_type: str
    student_label: str
    captured_at: str
    page_state: str
    page_markdown: str
    fields: list[FieldObservation] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        profile_type: str,
        student_label: str,
        page_state: str,
        page_markdown: str,
    ) -> "ProfileSnapshot":
        if profile_type not in PROFILE_TYPES:
            raise ValueError(f"Unsupported profile type: {profile_type}")
        return cls(
            profile_type=profile_type,
            student_label=student_label,
            captured_at=datetime.now(timezone.utc).isoformat(),
            page_state=page_state,
            page_markdown=page_markdown,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Comparison:
    profile_type: str
    field_key: str
    label: str
    portal_value: Any
    source_value: Any
    source_system: str | None
    status: str
    proposed_value: Any
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
