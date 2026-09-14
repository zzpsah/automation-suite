#!/usr/bin/env python3
"""Deliver published documents safely through eLettersBot.

Stage 10 adds durable per-document/per-chat delivery state, a database claim
lock, staged message/document progress, bounded Telegram retries, recovery
of legacy audit-only deliveries, and final-state reflection into the original
UMVInputBot progress message.
"""
from __future__ import annotations

import hashlib
import html
import io
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

import boto3
import requests

from telegram_file_delivery import prepare_delivery

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_OUTPUT_BOT_TOKEN"]
INPUT_TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
EXPECTED_BOT_USERNAME = os.environ.get("TELEGRAM_OUTPUT_BOT_USERNAME", "eLettersBot").lstrip("@").lower()
CONFIGURED_CHAT_IDS = [x.strip() for x in os.environ.get("TELEGRAM_NOTIFICATION_CHAT_IDS", "").split(",") if x.strip()]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APPLICATION_KEY"]
B2_BUCKET = os.environ.get("B2_BUCKET_NAME", "Education-Dept-Files")
B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"
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


def db_patch(path, payload):
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=representation"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def db_rpc(name, payload):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/{name}",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
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


def telegram(method, payload=None, files=None, token=None):
    bot_token = token or TELEGRAM_TOKEN
    r = requests.post(
        f"https://api.telegram.org/bot{bot_token}/{method}",
        data=payload,
        files=files,
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description") or f"Telegram {method} failed")
    return data.get("result")


def update_input_progress(doc, delivery_state):
    """Edit the original UMVInputBot progress message using the input-bot token."""
    if not INPUT_TELEGRAM_TOKEN:
        print("Input-bot progress skipped: TELEGRAM_BOT_TOKEN not configured")
        return False
    intake_rows = find_intake_for_document(doc)
    if not intake_rows:
        print(f"Input-bot progress skipped document={doc.get('id')}: no intake")
        return False
    intake = intake_rows[0]
    chat_id = str(intake.get("telegram_chat_id") or "").strip()
    message_id = intake.get("progress_message_id")
    if not chat_id or not message_id:
        print(f"Input-bot progress skipped document={doc.get('id')}: missing chat/message")
        return False
    status = str((delivery_state or {}).get("status") or "pending")
    attempts = (delivery_state or {}).get("attempts") or 0
    filename = html.escape(str((delivery_state or {}).get("filename") or doc.get("display_filename") or doc.get("original_filename") or "document"), quote=False)
    if status == "sent":
        text = (
            "✅ <b>दस्तावेज़ प्रकाशित और eLettersBot से भेज दिया गया</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🟢 <b>Stage 10 — eLettersBot:</b> Sent\n"
            f"🔁 <b>Attempts:</b> {attempts}\n"
            f"🆔 <b>Telegram document message:</b> {(delivery_state or {}).get('document_message_id') or '—'}\n"
            f"🕒 <b>Sent:</b> {html.escape(str((delivery_state or {}).get('sent_at') or '—'), quote=False)}"
        )
    elif status == "failed":
        text = (
            "⚠️ <b>दस्तावेज़ प्रकाशित, लेकिन eLettersBot delivery विफल</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🔴 <b>Stage 10 — eLettersBot:</b> Failed\n"
            f"🔁 <b>Attempts:</b> {attempts}\n"
            f"❌ <b>Error:</b> {html.escape(str((delivery_state or {}).get('last_error') or 'Delivery failed'), quote=False)}"
        )
    elif status == "message_sent":
        text = (
            "📤 <b>दस्तावेज़ प्रकाशित</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🟡 <b>Stage 10 — eLettersBot:</b> Sending document…\n"
            f"🔁 <b>Attempts:</b> {attempts}"
        )
    else:
        text = (
            "📤 <b>दस्तावेज़ प्रकाशित</b>\n\n"
            f"📄 <b>फ़ाइल:</b> {filename}\n"
            "🔵 <b>Stage 10 — eLettersBot:</b> Delivery queued\n"
            f"🔁 <b>Attempts:</b> {attempts}"
        )
    telegram(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        },
        token=INPUT_TELEGRAM_TOKEN,
    )
    print(f"Input-bot progress updated document={doc.get('id')} message={message_id} status={status}")
    return True
