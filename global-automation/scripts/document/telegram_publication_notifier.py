#!/usr/bin/env python3
"""Notify Telegram recipients after a document is finally published.

Notification is deliberately separate from publication: a Telegram failure must
never roll back a successfully published document. Audit rows make delivery
idempotent and retryable.
"""
import html
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote

import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_OUTPUT_BOT_TOKEN"]
CONFIGURED_CHAT_IDS = [x.strip() for x in os.environ.get("TELEGRAM_NOTIFICATION_CHAT_IDS", "").split(",") if x.strip()]
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

TAG_MAP = {
    "admission": ["#नामांकन", "#SpotAdmission", "#OFSS", "#Admission"],
    "bseb": ["#BSEB", "#बिहारविद्यालयपरीक्षासमिति", "#Board"],
    "academic": ["#Academic", "#शैक्षणिक", "#विद्यालय"],
    "exam": ["#Exam", "#परीक्षा", "#BSEB"],
    "scholarship": ["#Scholarship", "#छात्रवृत्ति", "#Student"],
    "salary": ["#Salary", "#वेतन", "#Finance"],
    "service": ["#Service", "#सेवा", "#Teacher"],
    "establishment": ["#Establishment", "#स्थापना", "#Office"],
    "training": ["#Training", "#प्रशिक्षण", "#Teacher"],
    "transfer": ["#Transfer", "#स्थानांतरण", "#Service"],
    "holiday": ["#Holiday", "#अवकाश", "#School"],
    "other": ["#OfficialDocument", "#सरकारीदस्तावेज"],
}


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
    return html.escape(str(value or "—"), quote=False)


def display_date(value):
    if not value:
        return "पहचान नहीं हो सकी"
    return str(value)[:10]


def tags_for(doc):
    category_key = str(doc.get("category_key") or "other").strip().lower()
    tags = TAG_MAP.get(category_key, TAG_MAP["other"])
    subject = str(doc.get("subject") or "").lower()
    if "नामांकन" in subject or "admission" in subject or "spot" in subject:
        tags = list(dict.fromkeys(tags + ["#नामांकन", "#Admission"]))
    if "परीक्षा" in subject or "exam" in subject:
        tags = list(dict.fromkeys(tags + ["#परीक्षा", "#Exam"]))
    return " ".join(tags[:8])


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


def format_message(doc, serial_no):
    authority = doc.get("issuing_authority")
    if not authority or str(authority).strip().lower() in {"unknown", "n/a", "na", "—"}:
        authority = "जारीकर्ता पहचान नहीं हो सका"

    short_description = doc.get("short_description") or "दस्तावेज़ के विषय के आधार पर संक्षिप्त विवरण उपलब्ध नहीं है।"
    subject = doc.get("subject") or "विषय पहचान नहीं हो सका"
    category = doc.get("category") or doc.get("category_key") or "अन्य"

    return (
        "<b>📢 नया सरकारी दस्तावेज़ प्रकाशित</b>\n\n"
        f"<b>क्रमांक:</b> {serial_no}\n"
        f"<b>जारी तिथि:</b> {esc(display_date(doc.get('normalized_issue_date')))}\n"
        f"<b>अपलोड तिथि:</b> {esc(display_date(doc.get('received_at') or doc.get('published_at')))}\n"
        f"<b>जारीकर्ता विभाग/प्राधिकरण:</b> {esc(authority)}\n\n"
        f"<b>विषय:</b> {esc(subject)}\n\n"
        f"<b>यह किस बारे में है:</b> {esc(short_description)}\n\n"
        f"<b>प्रकार:</b> {esc(category)}\n"
        f"<b>खोज टैग:</b> {esc(tags_for(doc))}\n\n"
        f"<b>पत्रांक:</b> {esc(doc.get('reference_number'))}\n"
        f"<b>फ़ाइल:</b> {esc(doc.get('display_filename') or doc.get('original_filename'))}\n\n"
        f"🔗 <b>दस्तावेज़ देखें:</b> {esc(doc.get('public_file_url'))}"
    )


def main():
    rows = db_get(
        "documents?select=id,original_filename,display_filename,subject,short_description,issuing_authority,reference_number,normalized_issue_date,received_at,published_at,category,category_key,public_file_url,publication_status,approved_for_publication&publication_status=eq.Published&approved_for_publication=is.true&order=received_at.desc.nullslast,published_at.desc.nullslast,normalized_issue_date.desc.nullslast&limit=50"
    )
    sent = failed = skipped = 0
    for serial_index, doc in enumerate(rows, start=1):
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
        message = format_message(doc, serial_index)
        for chat_id in targets:
            if already_sent(doc["id"], chat_id):
                continue
            try:
                telegram("sendMessage", {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False})
                telegram("sendDocument", {"chat_id": chat_id, "document": doc["public_file_url"], "caption": f"📎 {doc.get('display_filename') or doc.get('original_filename') or 'Published document'}"})
                db_insert_audit({
                    "document_id": doc["id"],
                    "operation": "telegram_publication_notification",
                    "actor_type": "system",
                    "from_status": {"publication_status": "Published"},
                    "to_status": {"telegram": "Sent"},
                    "details": {"chat_id": chat_id, "sent_at": datetime.now(timezone.utc).isoformat(), "serial_no": serial_index},
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
