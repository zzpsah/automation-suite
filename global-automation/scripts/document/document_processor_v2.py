#!/usr/bin/env python3
"""Process stored Telegram PDF documents with the reusable Sarkari OCR engine."""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import sys
import tempfile
import uuid
from pathlib import Path

import boto3
import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ocr.ocr_engine import extract_document_text
from ocr.sarkari_normalizer import extract_metadata

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APPLICATION_KEY"]
B2_BUCKET = os.environ.get("B2_BUCKET_NAME", "Education-Dept-Files")
B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def db_get(path: str):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def db_patch(table: str, rid: str, payload: dict):
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{rid}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def db_insert(payload: dict):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/documents",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=representation"},
        json=payload,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase documents insert {r.status_code}: {r.text[:1200]}")
    data = r.json()
    return data[0] if data else payload


def b2_client():
    return boto3.client(
        "s3", endpoint_url=B2_ENDPOINT, region_name="us-east-005",
        aws_access_key_id=B2_KEY_ID, aws_secret_access_key=B2_APP_KEY,
    )


def is_pdf(row: dict) -> bool:
    mime = (row.get("mime_type") or "").lower()
    name = (row.get("file_name") or "").lower()
    return mime == "application/pdf" or name.endswith(".pdf")


def process(row: dict) -> bool:
    rid = row["id"]
    metadata = row.get("metadata") or {}
    storage = metadata.get("storage") or {}
    key = storage.get("b2_key")
    if not key or storage.get("b2_status") != "AVAILABLE":
        raise RuntimeError("Verified B2 object is missing")

    existing = db_get(
        f"documents?select=id&source_app=eq.UMVInputBot&source_message_id=eq.{rid}&limit=1"
    )
    if existing:
        db_patch("telegram_intake", rid, {"status": "Processed", "metadata": {**metadata, "document_id": existing[0]["id"]}})
        return False

    obj = b2_client().get_object(Bucket=B2_BUCKET, Key=key)
    data = obj["Body"].read()
    if not data:
        raise RuntimeError("B2 object is empty")

    digest = hashlib.sha256(data).hexdigest()
    if storage.get("sha256") and digest != storage["sha256"]:
        raise RuntimeError("B2 SHA-256 verification failed")

    filename = row.get("file_name") or "document.pdf"
    with tempfile.TemporaryDirectory() as workdir:
        pdf_path = Path(workdir) / filename
        pdf_path.write_bytes(data)
        text, method = extract_document_text(str(pdf_path), workdir)

    if not text.strip():
        raise RuntimeError("No text could be extracted from PDF")

    md = extract_metadata(text)
    subject = md.subject or filename
    category_key = md.category or "other"
    category = {
        "admission": "Admission", "examination": "Examination", "bseb": "BSEB",
        "student": "Student", "staff": "Staff", "other": "Other",
    }.get(category_key, "Other")
    short = subject[:500]
    detailed = (
        f"यह दस्तावेज़ {filename} के रूप में प्राप्त हुआ। "
        f"विषय: {subject}. "
        f"जारीकर्ता: {md.authority or 'स्वतः निर्धारित नहीं हो सका'}. "
        f"जारी तिथि: {md.issue_date or 'स्वतः निर्धारित नहीं हो सकी'}. "
        f"OCR/दस्तावेज़-पाठ निष्कर्षण के आधार पर विवरण तैयार किया गया है।"
    )[:4000]

    payload = {
        "id": str(uuid.uuid4()), "source_app": "UMVInputBot", "source_location": "Telegram",
        "source_message_id": str(rid), "original_filename": filename, "display_filename": filename,
        "mime_type": row.get("mime_type"), "file_size": len(data), "file_checksum": digest,
        "private_drive_file_id": storage.get("drive_file_id"),
        "private_drive_url": f"https://drive.google.com/file/d/{storage.get('drive_file_id')}/view" if storage.get("drive_file_id") else None,
        "public_file_url": "", "reference_number": md.reference_number,
        "issue_date_as_printed": md.issue_date, "normalized_issue_date": None,
        "received_at": row.get("received_at"), "issuing_authority": md.authority,
        "subject": subject, "short_description": short, "detailed_summary": detailed,
        "category": category, "subcategory": None, "priority": "NORMAL", "required_action": "None",
        "deadline_as_printed": None, "normalized_deadline": None, "affected_entities": [],
        "financial_amount": None, "full_text_ocr": text, "extraction_method": method,
        "extraction_confidence": md.confidence, "sensitive": False, "useful": True, "duplicate": False,
        "duplicate_reason": None, "processing_status": "Completed", "forwarding_status": "Not Forwarded",
        "approved_for_publication": False, "category_key": category_key, "category_source": "rule",
        "category_confidence": "HIGH" if category_key != "other" else "LOW",
        "ai_suggestion_status": "Not Requested", "publication_status": "Unpublished",
        "publication_reason": "Awaiting publication workflow", "public_revision": 0,
    }
    created = db_insert(payload)
    actual_id = created.get("id", payload["id"])
    db_patch("telegram_intake", rid, {
        "status": "Processed",
        "metadata": {**metadata, "document_id": actual_id,
                     "processed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "ocr_engine": "global-sarkari-ocr", "ocr_method": method},
    })
    print(f"Processed {rid} -> {actual_id} via {method} ({md.confidence})")
    return True


def main() -> int:
    rows = db_get(
        "telegram_intake?select=*&or=(status.eq.Stored,status.eq.Processing%20Failed)"
        "&order=received_at.asc&limit=25"
    )
    # /text and other non-file intake records are intentionally left alone for a future text path.
    candidates = [row for row in rows if is_pdf(row)]
    skipped = len(rows) - len(candidates)
    processed = failed = 0
    for row in candidates:
        try:
            if process(row):
                processed += 1
        except Exception as exc:
            failed += 1
            md = row.get("metadata") or {}
            db_patch("telegram_intake", row["id"], {
                "status": "Processing Failed",
                "metadata": {**md, "processing_error": str(exc)[:1200],
                             "processing_error_at": dt.datetime.now(dt.timezone.utc).isoformat()},
            })
            print(f"Record {row['id']}: processing failed: {exc}")
    print(f"Document processor complete: processed={processed}, failed={failed}, candidates={len(candidates)}, skipped_non_files={skipped}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
