#!/usr/bin/env python3
"""Reconcile published documents that still need Telegram delivery.

This is deliberately recipient-scoped: one failed delivery never blocks another.
The notifier remains the delivery executor; this module produces a deterministic
work list and records no external side effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DeliveryWorkItem:
    document_id: str
    chat_id: str
    reason: str


def is_published(doc: dict[str, Any]) -> bool:
    return doc.get("publication_status") == "Published" and doc.get("approved_for_publication") is True


def needs_delivery(doc: dict[str, Any], chat_id: str, audit_rows: list[dict[str, Any]]) -> bool:
    if not is_published(doc) or not chat_id:
        return False
    return not any(
        str(row.get("document_id")) == str(doc.get("id"))
        and str(row.get("operation")) == "telegram_publication_notification"
        and str((row.get("details") or {}).get("chat_id")) == str(chat_id)
        and str((row.get("details") or {}).get("result", "Sent")) == "Sent"
        for row in audit_rows
    )


def build_worklist(documents: list[dict[str, Any]], chat_ids: list[str], audits: list[dict[str, Any]]) -> list[DeliveryWorkItem]:
    """Build a stable document/recipient worklist without sending anything."""
    result: list[DeliveryWorkItem] = []
    for doc in documents:
        for chat_id in dict.fromkeys(str(x).strip() for x in chat_ids if str(x).strip()):
            if needs_delivery(doc, chat_id, audits):
                result.append(DeliveryWorkItem(str(doc["id"]), chat_id, "published_and_not_successfully_delivered"))
    return result


def reconciliation_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
