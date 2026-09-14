#!/usr/bin/env python3
"""Deliver exactly one published document through the durable eLettersBot path."""
from __future__ import annotations

import hashlib
import os
import sys
from urllib.parse import quote

from telegram_file_delivery import prepare_delivery
import telegram_publication_notifier_v3 as base

DOCUMENT_ID = os.environ.get("DOCUMENT_ID", "").strip()


def get_document(did: str):
    rows = base.db_get(
        "documents?select=id,source_message_id,original_filename,display_filename,subject,short_description,"
        "issuing_authority,reference_number,normalized_issue_date,received_at,published_at,category,category_key,"
        "publication_status,approved_for_publication&id=eq." + quote(did, safe="") + "&limit=1"
    )
    return rows[0] if rows else None


def main() -> int:
    if not DOCUMENT_ID:
        print("DOCUMENT_ID is required")
        return 2
    base.verify_output_bot()
    doc = get_document(DOCUMENT_ID)
    if not doc:
        print(f"Document not found: {DOCUMENT_ID}")
        return 2
    if doc.get("publication_status") != "Published" or doc.get("approved_for_publication") is not True:
        print(f"Document is not published/approved: {DOCUMENT_ID}")
        return 2

    intake = base.find_intake_for_document(doc)
    if not intake:
        print("No Telegram intake linked")
        return 2
    row = intake[0]
    object_key = ((row.get("metadata") or {}).get("storage") or {}).get("b2_key")
    if not object_key:
        print("B2 object key missing")
        return 2
    targets = base.recipients(intake)
    if not targets:
        print("No Telegram recipients configured")
        return 2

    source = base.b2_download(object_key)
    source_sha = hashlib.sha256(source).hexdigest()
    expected = base.expected_sha256(row)
    if expected and expected != source_sha:
        raise RuntimeError(f"B2 checksum mismatch: expected={expected}, actual={source_sha}")
    delivery = prepare_delivery(
        source,
        row.get("file_name") or doc.get("original_filename") or "document",
        row.get("mime_type") or "",
    )
    delivery_sha = hashlib.sha256(delivery["data"]).hexdigest()
    print(
        f"document={DOCUMENT_ID} source={delivery['source_format']} delivery={delivery['delivery_format']} "
        f"converted={delivery['converted']} pages={delivery['pages']} bytes={len(delivery['data'])}"
    )

    message = base.format_message(doc)
    sent = skipped = locked = 0
    for chat_id in targets:
        if base.already_sent(DOCUMENT_ID, chat_id):
            base.mark_legacy_sent(DOCUMENT_ID, chat_id)
            skipped += 1
            continue
        result = base.deliver_one(doc, chat_id, message, delivery, source_sha, delivery_sha)
        if result == "sent":
            sent += 1
        elif result in {"already_sent", "locked"}:
            if result == "locked":
                locked += 1
            else:
                skipped += 1

    print(f"Targeted Telegram notifier: sent={sent}, skipped={skipped}, locked={locked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
