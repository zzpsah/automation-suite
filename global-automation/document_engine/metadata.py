"""Stable metadata assembly from OCR/extraction evidence."""
from __future__ import annotations
from typing import Any


def build_metadata(filename: str, ocr: dict[str, Any], fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "filename": filename,
        "subject": fields.get("subject"),
        "authority": fields.get("authority"),
        "reference": fields.get("reference"),
        "date": fields.get("date"),
        "bihar_office": ocr.get("bihar_office"),
        "ocr_backend": ocr.get("backend") or ocr.get("extraction_method"),
        "source_preserved": True,
    }
