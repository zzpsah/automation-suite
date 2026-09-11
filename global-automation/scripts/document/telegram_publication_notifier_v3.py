#!/usr/bin/env python3
"""Deliver published PDFs through the dedicated eLettersBot.

Uses the intake row referenced by documents.source_message_id to locate the
private B2 object. PDF bytes are uploaded directly to Telegram; no storage URL
is included in the notification.
"""
import html
import io
import os
import sys
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

import boto3
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_OUTPUT_BOT_TOKEN"]
EXPECTED_BOT_USERNAME = os.environ.get("TELEGRAM_OUTPUT_BOT_USERNAME", "eLettersBot").lstrip("@").lower()
CONFIGURED_CHAT_IDS = [x.strip() for x in os.environ.get("TELEGRAM_NOTIFICATION_CHAT_IDS", "").split(",") if x.strip()]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APPLICATION_KEY"]
B2_BUCKET = os.environ.get("B2_BUCKET_NAME", "Education-Dept-Files")
DEFAULT_B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"
_configured_endpoint = (os.environ.get("B2_S3_ENDPOINT") or "").strip().strip('"').strip("'")
_parsed_endpoint = urlparse(_configured_endpoint)
B2_ENDPOINT = _configured_endpoint if _parsed_endpoint.scheme in {"http", "https"} and _parsed_endpoint.netloc else DEFAULT_B2_ENDPOINT
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
    r = requests.post(f"{SUPABASE_URL}/rest/v1/document_operations_audit", headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"}, json=payload, timeout=30)
    r.raise_for_status()


def telegram(method, payload=None, files=None):
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}", data=payload, files=files, timeout=120)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method}: {data.get('description', 'unknown error')}")
    return data.get("result")


def verify_output_bot():
    me = telegram("getMe")
    username = str(me.get("username") or "").lstrip("@").lower()
    if username != EXPECTED_BOT_USERNAME:
        raise RuntimeError(f"Wrong Telegram output bot: @{username or 'unknown'}; expected @{EXPECTED_BOT_USERNAME}")
    print(f"Telegram output bot verified: @{username}")


def b2_client():
    return boto3.client("s3", endpoint_url=B2_ENDPOINT, aws_access_key_id=B2_KEY_ID, aws_secret_access_key=B2_APP_KEY, region_name="us-east-005")


def b2_download(object_key):
    buf = io.BytesIO()
    b2_client().download_fileobj(B2_BUCKET, object_key, buf)
    data = buf.getvalue()
    if not data:
        raise RuntimeError(f"B2 returned empty object: {object_key}")
    return data


def esc(value):
    return html.escape(str(value or "—"), quote=False)


def display_date(value):
    return str(value)[:10] if value else "पहचान नहीं हो सकी"


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
    q = ("document_operations_audit?select=id&document_id=eq." + quote(str(document_id), safe="") + "&operation=eq.telegram_publication_notification&details->>chat_id=eq." + quote(str(chat_id), safe="") + "&limit=1")
    return bool(db_get(q))


def format_message(doc, serial_no):
    authority = doc.get("issuing_authority") or "जारीकर्ता पहचान नहीं हो सका"
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
        "📎 PDF नीचे संलग्न है — कोई बाहरी डाउनलोड लिंक नहीं।"
    )


def find_intake_for_document(doc):
    source_message_id = str(doc.get("source_message_id") or "").strip()
    if not source_message_id:
        return []
    # Only UUID-shaped source_message_id values can be telegram_intake primary keys.
    # Legacy rows may contain values such as chat_id:message_id; skip those safely.
    try:
        uuid.UUID(source_message_id)
    except ValueError:
        return []
    return db_get("telegram_intake?select=id,telegram_chat_id,metadata&limit=1&id=eq." + quote(source_message_id, safe=""))


def main():
    verify_output_bot()
    rows = db_get("documents?select=id,source_message_id,original_filename,display_filename,subject,short_description,issuing_authority,reference_number,normalized_issue_date,received_at,published_at,category,category_key,publication_status,approved_for_publication&publication_status=eq.Published&approved_for_publication=is.true&order=received_at.desc.nullslast,published_at.desc.nullslast,normalized_issue_date.desc.nullslast&limit=50")
    sent = failed = skipped = 0
    serial_no = 0
    print(f"B2 endpoint configured: {urlparse(B2_ENDPOINT).netloc}")
    for doc in rows:
        intake = find_intake_for_document(doc)
        if not intake:
            skipped += 1
            print(f"Skipping document={doc['id']}: no valid telegram_intake linkage")
            continue
        object_key = ((intake[0].get("metadata") or {}).get("storage") or {}).get("b2_key")
        if not object_key:
            skipped += 1
            print(f"Skipping document={doc['id']}: no B2 object key")
            continue
        serial_no += 1
        targets = recipients(intake)
        if not targets:
            skipped += 1
            print(f"Skipping document={doc['id']}: no Telegram recipients")
            continue
        try:
            pdf_data = b2_download(object_key)
        except Exception as exc:
            failed += 1
            print(f"B2 download failed for document={doc['id']}: {exc}")
            continue
        message = format_message(doc, serial_no)
        filename = doc.get("display_filename") or doc.get("original_filename") or "published-document.pdf"
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        for chat_id in targets:
            if already_sent(doc["id"], chat_id):
                continue
            try:
                telegram("sendMessage", payload={"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": "true"})
                telegram("sendDocument", payload={"chat_id": chat_id, "caption": f"📎 {filename}"}, files={"document": (filename, pdf_data, "application/pdf")})
                db_insert_audit({
                    "document_id": doc["id"], "operation": "telegram_publication_notification", "actor_type": "system",
                    "from_status": {"publication_status": "Published"}, "to_status": {"telegram": "Sent"},
                    "details": {"chat_id": chat_id, "bot_username": EXPECTED_BOT_USERNAME, "delivery": "private_b2_to_telegram_multipart", "external_link_exposed": False, "sent_at": datetime.now(timezone.utc).isoformat(), "serial_no": serial_no},
                })
                sent += 1
                print(f"Notified @{EXPECTED_BOT_USERNAME} -> {chat_id} for {doc['id']}")
            except Exception as exc:
                failed += 1
                print(f"Notification failed for document={doc['id']} chat={chat_id}: {exc}")
    print(f"Telegram publication notifier: sent={sent}, failed={failed}, skipped={skipped}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
