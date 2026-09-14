#!/usr/bin/env python3
"""Reflect durable eLetters delivery state in the existing UMVInputBot progress message."""
from __future__ import annotations

import html
import os
import sys
from urllib.parse import quote

import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_INPUT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DOCUMENT_ID = str(os.environ.get("DOCUMENT_ID") or "").strip()
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def db_get(path: str):
    response = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def telegram(method: str, payload: dict):
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_INPUT_TOKEN}/{method}",
        data=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description") or f"Telegram {method} failed")
    return data.get("result")


def esc(value) -> str:
    return html.escape(str(value or ""), quote=False)


def progress_text(delivery: dict) -> str:
    status = str(delivery.get("status") or "pending")
    filename = esc(delivery.get("filename") or "document")
    attempts = delivery.get("attempts") or 0
    if status == "sent":
        document_message_id = delivery.get("document_message_id")
        sent_at = esc(delivery.get("sent_at") or "")
        return (
            "✅ <b>दस्तावेज़ प्रकाशित और eLettersBot से भेज दिया गया</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🟢 <b>Stage 10 — eLettersBot:</b> Sent\n"
            f"🔁 <b>Attempts:</b> {attempts}\n"
            f"🆔 <b>Telegram document message:</b> {document_message_id or '—'}\n"
            f"🕒 <b>Sent:</b> {sent_at or '—'}"
        )
    if status == "failed":
        error = esc(delivery.get("last_error") or "Delivery failed")
        return (
            "⚠️ <b>दस्तावेज़ प्रकाशित, लेकिन eLettersBot delivery विफल</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🔴 <b>Stage 10 — eLettersBot:</b> Failed\n"
            f"🔁 <b>Attempts:</b> {attempts}\n"
            f"❌ <b>Error:</b> {error}"
        )
    if status == "message_sent":
        return (
            "📤 <b>दस्तावेज़ प्रकाशित</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🟡 <b>Stage 10 — eLettersBot:</b> Sending document…\n"
            f"🔁 <b>Attempts:</b> {attempts}"
        )
    return (
        "📤 <b>दस्तावेज़ प्रकाशित</b>\n\n"
        f"📄 <b>फ़ाइल:</b> {filename}\n"
        "🔵 <b>Stage 10 — eLettersBot:</b> Delivery queued\n"
        f"🔁 <b>Attempts:</b> {attempts}"
    )


def target_rows():
    base = (
        "telegram_publication_deliveries?select=document_id,chat_id,status,attempts,message_id,document_message_id,"
        "last_error,filename,sent_at&limit=100"
    )
    if DOCUMENT_ID:
        base += "&document_id=eq." + quote(DOCUMENT_ID, safe="")
    return db_get(base + "&order=updated_at.desc")


def intake_for_document(document_id: str):
    return db_get(
        "telegram_intake?select=id,telegram_chat_id,progress_message_id,status,document_id&limit=1&document_id=eq."
        + quote(str(document_id), safe="")
    )


def main() -> int:
    rows = target_rows()
    if DOCUMENT_ID and not rows:
        raise RuntimeError(f"No durable eLetters delivery row found for document={DOCUMENT_ID}")

    updated = failed = skipped = 0
    for row in rows:
        intake_rows = intake_for_document(str(row.get("document_id") or ""))
        if not intake_rows:
            skipped += 1
            continue
        intake = intake_rows[0]
        chat_id = str(intake.get("telegram_chat_id") or row.get("chat_id") or "").strip()
        message_id = intake.get("progress_message_id")
        if not chat_id or not message_id:
            skipped += 1
            continue
        try:
            result = telegram(
                "editMessageText",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": progress_text(row),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": "true",
                },
            )
            updated += 1
            print(
                f"UMVInputBot progress updated: document={row.get('document_id')} "
                f"chat_id={chat_id} message_id={message_id} delivery_status={row.get('status')} "
                f"result_message_id={(result or {}).get('message_id')}"
            )
        except Exception as exc:
            failed += 1
            print(
                f"Progress update failed document={row.get('document_id')} chat={chat_id} "
                f"message={message_id}: {exc}"
            )

    print(f"Telegram delivery progress: updated={updated}, failed={failed}, skipped={skipped}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
