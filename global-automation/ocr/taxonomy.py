"""Versioned, project-agnostic government-document taxonomy."""
from __future__ import annotations

TAXONOMY_VERSION = "1.0"

CATEGORIES = {
    "admission": "Admission / Enrollment",
    "examination": "Examination / Result",
    "bseb": "Board / BSEB",
    "student": "Student",
    "staff": "Staff / Teacher",
    "other": "Other Government Document",
}


def normalize_category(category: str | None) -> str:
    """Return a stable taxonomy key without inventing a new category."""
    value = (category or "").strip().lower()
    return value if value in CATEGORIES else "other"


def taxonomy_info(category: str | None) -> dict[str, str]:
    key = normalize_category(category)
    return {"version": TAXONOMY_VERSION, "key": key, "label": CATEGORIES[key]}
