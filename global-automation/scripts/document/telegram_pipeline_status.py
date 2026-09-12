#!/usr/bin/env python3
"""Telegram pipeline status message contract.

The worker updates one status message per intake record. Delivery is intentionally
best-effort and idempotent: callers should persist telegram_status_message_id in
telegram_intake.metadata.telegram_status before calling again.

This module is a contract/helper for pipeline workers; it never invents a stage.
"""
from __future__ import annotations

STATUS_TEXT = {
    "Received": "📥 File received\nStatus: Received",
    "Storage Uploading": "☁️ File received\nStatus: Uploading to secure storage…",
    "Stored": "☁️ Storage complete\nStatus: Stored in B2 (backup verified)",
    "Processing": "🔎 Document processing\nStatus: GovDOC Vision OCR in progress…",
    "Completed": "🧠 Document processed\nStatus: OCR + metadata extraction complete",
    "Published": "📢 Document published\nStatus: Ready for delivery",
    "Delivered": "🤖 eLettersBot delivery complete\nStatus: PDF delivered ✅",
    "Failed": "❌ Document processing failed\nStatus: Retry will be attempted automatically",
}


def render(stage: str, detail: str | None = None) -> str:
    """Render only a known pipeline stage; optional detail is bounded."""
    text = STATUS_TEXT.get(stage)
    if not text:
        raise ValueError(f"Unknown pipeline stage: {stage}")
    if detail:
        text += "\n\n" + str(detail)[:700]
    return text
