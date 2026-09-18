from __future__ import annotations

import re
from typing import Any

from models import Comparison


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def _compact(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", _norm(value))


def compare_value(
    *,
    profile_type: str,
    field_key: str,
    label: str,
    portal_value: Any,
    source_value: Any,
    source_system: str | None = None,
) -> Comparison:
    p = _norm(portal_value)
    s = _norm(source_value)

    if not p and not s:
        status = "NOT_AVAILABLE"
        proposed = None
    elif not p and s:
        status = "MISSING_IN_PORTAL"
        proposed = source_value
    elif p and not s:
        status = "MISSING_IN_SOURCE"
        proposed = None
    elif p == s:
        status = "MATCH"
        proposed = portal_value
    elif _compact(portal_value) == _compact(source_value):
        status = "MINOR_VARIATION"
        proposed = source_value
    else:
        status = "VALUE_DIFFERENT"
        proposed = source_value

    return Comparison(
        profile_type=profile_type,
        field_key=field_key,
        label=label,
        portal_value=portal_value,
        source_value=source_value,
        source_system=source_system,
        status=status,
        proposed_value=proposed,
    )


def compare_profiles(
    portal: dict[str, Any],
    source: dict[str, Any],
    source_system: str = "approved_source",
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for profile_type in ("general", "education", "facility"):
        portal_fields = portal.get(profile_type, {}) or {}
        source_fields = source.get(profile_type, {}) or {}
        keys = sorted(set(portal_fields) | set(source_fields))
        for key in keys:
            result = compare_value(
                profile_type=profile_type,
                field_key=key,
                label=key.replace("_", " ").title(),
                portal_value=portal_fields.get(key),
                source_value=source_fields.get(key),
                source_system=source_system,
            )
            results.append(result.to_dict())
    return results
