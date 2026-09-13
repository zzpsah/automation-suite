#!/usr/bin/env python3
"""Deliver exactly one published document through eLettersBot."""
from __future__ import annotations
import hashlib, os, sys
from datetime import datetime, timezone
from urllib.parse import quote
import requests
from telegram_file_delivery import prepare_delivery
import telegram_publication_notifier_v3 as base

DOCUMENT_ID = os.environ.get("DOCUMENT_ID", "").strip()


def get_document(did: str):
    rows = base.db_get(
        "documents?select=id,source_message_id,original_filename,display_filename,subject,short_description,"
        "issuing_authority,reference_number,normalized_issue_date,received_at,published_at,category,category_key,"
        "publication_status,approved_for_publication,sensitive,duplicate,useful,extraction_confidence,"
        "private_drive_file_id,full_text_ocr,extraction_method&id=eq." + quote(did, safe="") + "&limit=1"
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
    actual_sha = hashlib.sha256(source).hexdigest()
    expected = base.expected_sha256(row)
    if expected and expected != actual_sha:
        raise RuntimeError(f"B2 checksum mismatch: expected={expected}, actual={actual_sha}")
    delivery = prepare_delivery(source, row.get("file_name") or doc.get("original_filename") or "document", row.get("mime_type") or "")
    delivery_sha = hashlib.sha256(delivery["data"]).hexdigest()
    print(f"document={DOCUMENT_ID} source={delivery['source_format']} delivery={delivery['delivery_format']} converted={delivery['converted']} pages={delivery['pages']} bytes={len(delivery['data'])}")

    sent = skipped = 0
    message = base.format_message(doc)
    for chat_id in targets:
        if base.already_sent(DOCUMENT_ID, chat_id):
            skipped += 1
            continue
        base.telegram("sendMessage", payload={"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": "true"})
        base.telegram("sendDocument", payload={"chat_id": chat_id, "caption": f"📎 {delivery['filename']}"}, files={"document": (delivery['filename'], delivery['data'], delivery['mime_type'])})
        base.db_insert_audit({"document_id": DOCUMENT_ID, "operation": "telegram_publication_notification", "actor_type": "system", "from_status": {"publication_status": "Published"}, "to_status": {"telegram": "Sent"}, "details": {"chat_id": chat_id, "bot_username": base.EXPECTED_BOT_USERNAME, "delivery_format_version": 2, "source_format": delivery["source_format"], "delivery_format": delivery["delivery_format"], "converted": delivery["converted"], "pages": delivery["pages"], "source_sha256": actual_sha, "delivery_sha256": delivery_sha, "bytes": len(delivery["data"]), "filename": delivery["filename"], "mime_type": delivery["mime_type"], "sent_at": datetime.now(timezone.utc).isoformat()}})
        sent += 1

    print(f"Targeted Telegram notifier: sent={sent}, skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
