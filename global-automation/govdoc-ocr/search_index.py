"""Storage-neutral search records for downstream indexing.

This module does not persist data and does not require Supabase.
"""
from __future__ import annotations


def build_search_record(result: dict) -> dict:
    pages = result.get("pages") or []
    return {
        "filename": result.get("filename"),
        "text": result.get("text", ""),
        "normalized_text": result.get("normalized_text", ""),
        "subject": result.get("subject", ""),
        "authority": result.get("authority", ""),
        "category": result.get("category", "other"),
        "page_count": len(pages),
        "schema_version": result.get("schema_version"),
        "source": "govdoc-ocr",
    }
