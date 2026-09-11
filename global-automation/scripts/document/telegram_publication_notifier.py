#!/usr/bin/env python3
"""Notify Telegram recipients after a document is finally published.

Notification is deliberately separate from publication: a Telegram failure must
never roll back a successfully published document. Audit rows make delivery
idempotent and retryable.
"""
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote

import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CONFIGURED_CHAT_IDS = [x.strip() for x in os.environ.get("TELEGRAM_NOTIFICATION_CHAT_IDS", "").split(",") if x.strip()]
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def db_get(path):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def db_insert_audit(payload):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/document_operations_audit",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def telegram(method, payload):
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}", json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method}: {data.get('description', 'unknown error')}")
    return data.get("result")


def esc(value):
    return str(value or "—").replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


def recipients(intake_rows):
    ids = list(CONFIGURED_CHAT_IDS)
    for row in intake_rows:
        chat_id = str(row.get("telegram_chat_id") or "").strip()
        if chat_id and chat_id not in ids:
            ids.append(chat_id)
    return ids


def already_sent(document_id, chat_id):
    q = (
        "document_operations_audit?select=id&document_id=eq."
        + quote(str(document_id), safe="")
        + "&operation=eq.telegram_publication_notification&details->>chat_id=eq."
        + quote(str(chat_id), safe="")
        + "&limit=1"
    )
    return bool(db_get(q))


def format_message(doc):
    return (
        "<b>📢 Document Published</b>\n\n"
        f"<b>विषय:</b> {esc(doc.get('subject'))}\n"
        f"<b>जारीकर्ता:</b> {esc(doc.get('issuing_authority'))}\n"
        f"<b>पत्रांक:</b> {esc(doc.get('reference_number'))}\n"
        f"<b>जारी तिथि:</b> {esc(doc.get('normalized_issue_date'))}\n"
        f"<b>श्रेणी:</b> {esc(doc.get('category'))}\n"
        f"<b>फ़ाइल:</b> {esc(doc.get('display_filename') or doc.get('original_filename'))}\n\n"
        f"<b>Public Link:</b> {esc(doc.get('public_file_url'))}"
    )


def main():
    rows = db_get(
        "documents?select=id,original_filename,display_filename,subject,issuing_authority,reference_number,normalized_issue_date,category,public_file_url,publication_status,approved_for_publication&publication_status=eq.Published&approved_for_publication=is.true&order=published_at.desc&limit=50"
    )
    sent = failed = skipped = 0
    for doc in rows:
        if not doc.get("public_file_url"):
            skipped += 1
            continue
        intake = db_get(
            "telegram_intake?select=id,telegram_chat_id&document_id=eq."
            + quote(str(doc["id"]), safe="")
            + "&limit=20"
        )
        targets = recipients(intake)
        if not targets:
            skipped += 1
            continue
        message = format_message(doc)
        for chat_id in targets:
            if already_sent(doc["id"], chat_id):
                continue
            try:
                telegram("sendMessage", {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False})
                # Telegram can fetch the public URL directly; this sends the actual PDF/document
                # rather than making the recipient open the archive first.
                telegram("sendDocument", {"chat_id": chat_id, "document": doc["public_file_url"], "caption": f"📎 {doc.get('display_filename') or doc.get('original_filename') or 'Published document'}"})
                db_insert_audit({
                    "document_id": doc["id"],
                    "operation": "telegram_publication_notification",
                    "actor_type": "system",
                    "from_status": {"publication_status": "Published"},
                    "to_status": {"telegram": "Sent"},
                    "details": {"chat_id": chat_id, "sent_at": datetime.now(timezone.utc).isoformat()},
                })
                sent += 1
                print(f"Notified {chat_id} for {doc['id']}")
            except Exception as exc:
                failed += 1
                print(f"Notification failed for document={doc['id']} chat={chat_id}: {exc}")
    print(f"Telegram publication notifier: sent={sent}, failed={failed}, skipped={skipped}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
