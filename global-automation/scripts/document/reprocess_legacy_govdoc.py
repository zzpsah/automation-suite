#!/usr/bin/env python3
"""Reprocess legacy DRIVE_OCR_RULES documents in-place with GovDOC Vision.

This is a migration worker, not a second OCR engine. It reads the canonical
B2 object referenced by telegram_intake, runs GovDOC Vision, and replaces the
legacy OCR provenance on the existing documents row without creating a
second document record.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import boto3
import requests

ROOT = Path(__file__).resolve().parents[2]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document import document_processor as processor
from scripts.document import govdoc_ocr_adapter as govdoc

govdoc.install(processor)

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


def db_patch(table: str, record_id: str, payload: dict):
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{quote(str(record_id), safe='')}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def b2_client():
    return boto3.client(
        "s3", endpoint_url=B2_ENDPOINT, region_name="us-east-005",
        aws_access_key_id=B2_KEY_ID, aws_secret_access_key=B2_APP_KEY,
    )


def main() -> int:
    legacy = db_get(
        "documents?select=id,source_message_id,original_filename,extraction_method&"
        "extraction_method=eq.DRIVE_OCR_RULES&source_app=eq.UMVInputBot&limit=100"
    )
    if not legacy:
        print("GovDOC legacy migration: nothing to reprocess")
        return 0

    client = b2_client()
    migrated = 0
    failed = 0
    for doc in legacy:
        doc_id = doc["id"]
        msg_id = doc.get("source_message_id")
        try:
            intake = db_get(
                f"telegram_intake?select=id,file_name,mime_type,received_at,metadata&"
                f"id=eq.{quote(str(msg_id), safe='')}&limit=1"
            )
            if not intake:
                raise RuntimeError(f"telegram_intake row not found for source_message_id={msg_id}")
            row = intake[0]
            storage = (row.get("metadata") or {}).get("storage") or {}
            key = storage.get("b2_key")
            if not key or storage.get("b2_status") != "AVAILABLE":
                raise RuntimeError("verified B2 object is unavailable")

            data = client.get_object(Bucket=B2_BUCKET, Key=key)["Body"].read()
            if not data:
                raise RuntimeError("B2 object is empty")

            filename = row.get("file_name") or doc.get("original_filename") or "document.pdf"
            result = govdoc._run(data, filename)
            text = (result.get("text") or "").strip()
            if not text:
                raise RuntimeError("GovDOC returned no OCR text")

            subject, authority, ref_no, printed, normalized, short, detailed, category_key, category, confidence = processor.extract_metadata(text, filename)
            info = result.get("metadata") or {}
            dtype = info.get("document_type") or {}
            category_key = dtype.get("value") or category_key or "other"
            category = {
                "admission": "Admission", "examination": "Examination", "transfer": "Transfer",
                "service": "Service", "training": "Training", "scholarship": "Scholarship",
                "holiday": "Holiday", "other": "Other",
            }.get(category_key, category_key)
            category_confidence = dtype.get("confidence") or confidence
            subject = ((info.get("subject") or {}).get("value") or subject or None)
            authority = ((info.get("authority") or {}).get("value") or authority or None)
            short = result.get("short_description") or short or None

            payload = {
                "full_text_ocr": text,
                "extraction_method": result.get("extraction_method") or "GovDOC Vision",
                "extraction_confidence": category_confidence or "MEDIUM",
                "category_source": "GovDOC Vision",
                "category_key": category_key,
                "category": category,
                "category_confidence": category_confidence,
                "subject": subject,
                "issuing_authority": authority,
                "reference_number": ref_no or None,
                "issue_date_as_printed": printed or None,
                "normalized_issue_date": normalized or None,
                "short_description": short,
                "detailed_summary": detailed,
                "ai_model": None,
                "ai_suggested_json": info or None,
                "ai_suggested_at": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            db_patch("documents", doc_id, payload)
            metadata = dict(row.get("metadata") or {})
            metadata.pop("processing_error", None)
            metadata.pop("processing_error_at", None)
            metadata["document_id"] = doc_id
            metadata["ocr_engine"] = "GovDOC Vision"
            metadata["processed_at"] = datetime.now(timezone.utc).isoformat()
            db_patch("telegram_intake", row["id"], {"status": "Processed", "metadata": metadata})
            migrated += 1
            print(f"GovDOC migrated {doc_id} (message {msg_id})")
        except Exception as exc:
            failed += 1
            print(f"GovDOC migration failed {doc_id}: {exc}")

    print(f"GovDOC legacy migration complete: migrated={migrated} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
