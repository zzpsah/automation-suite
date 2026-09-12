#!/usr/bin/env python3
"""Read-only health checks for the School Document Pipeline.

The watchdog detects broken or stalled connections between Telegram intake,
B2 storage, document processing/OCR, publication, and Telegram delivery.
It never creates or mutates production document data.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests

BASE = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "zzpsah/automation-suite")

# Conservative thresholds: asynchronous processing is allowed some time, but
# a long absence of state movement is surfaced as a broken/stalled connection.
INTAKE_TO_B2_MINUTES = int(os.environ.get("INTAKE_TO_B2_MINUTES", "10"))
STORED_TO_DOCUMENT_MINUTES = int(os.environ.get("STORED_TO_DOCUMENT_MINUTES", "20"))
PROCESSING_STALE_MINUTES = int(os.environ.get("PROCESSING_STALE_MINUTES", "30"))
PUBLISHED_TO_DELIVERY_MINUTES = int(os.environ.get("PUBLISHED_TO_DELIVERY_MINUTES", "15"))


def get(path: str):
    r = requests.get(f"{BASE}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def age_minutes(value: str | None, now: datetime) -> float | None:
    dt = parse_dt(value)
    if not dt:
        return None
    return max(0.0, (now - dt).total_seconds() / 60.0)


def github_repository_dispatch_runs():
    if not GITHUB_TOKEN:
        return []
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs?event=repository_dispatch&per_page=30"
    r = requests.get(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("workflow_runs", [])


def is_canonical_telegram_document(row: dict) -> bool:
    return row.get("source_app") == "UMVInputBot" or row.get("source_location") == "Telegram"


def main() -> int:
    now = datetime.now(timezone.utc)
    cutoff24 = (now - timedelta(hours=24)).isoformat()
    cutoff48 = (now - timedelta(hours=48)).isoformat()

    intake = get(
        "telegram_intake?select=id,telegram_message_id,file_id,file_name,status,storage_status,storage_bucket,storage_path,document_id,received_at,metadata&"
        f"received_at=gte.{quote(cutoff24, safe='')}&order=received_at.desc&limit=500"
    )
    docs = get(
        "documents?select=id,source_app,source_location,source_message_id,original_filename,processing_status,publication_status,approved_for_publication,public_file_url,subject,issuing_authority,extraction_method,full_text_ocr,private_drive_file_id,received_at,updated_at,created_at&"
        f"received_at=gte.{quote(cutoff48, safe='')}&order=received_at.desc&limit=500"
    )
    audits = get(
        "document_operations_audit?select=document_id,operation,details,created_at&"
        f"created_at=gte.{quote(cutoff24, safe='')}&limit=2000"
    )

    intake_counts = Counter(str(r.get("status") or "NULL") for r in intake)
    doc_counts = Counter(str(r.get("processing_status") or "NULL") for r in docs if is_canonical_telegram_document(r))

    docs_by_source = {str(r["source_message_id"]): r for r in docs if r.get("source_message_id")}

    notified_document_ids = {
        str(a.get("document_id"))
        for a in audits
        if a.get("document_id")
        and a.get("operation") == "telegram_publication_notification"
    }

    issues: list[str] = []
    warnings: list[str] = []

    # Stage 1: Telegram -> Supabase -> B2.
    for row in intake:
        rid = str(row.get("id"))
        file_id = row.get("file_id")
        age = age_minutes(row.get("received_at"), now)
        storage_status = row.get("storage_status")
        if file_id and row.get("status") in {"Received", "Processing"}:
            if storage_status != "Stored" and age is not None and age > INTAKE_TO_B2_MINUTES:
                issues.append(
                    f"BROKEN TELEGRAM→B2: intake {rid} ({row.get('file_name') or 'file'}) has been {row.get('status')} for {age:.1f}m without Stored status"
                )
        if storage_status == "Stored" and (not row.get("storage_bucket") or not row.get("storage_path")):
            issues.append(f"BROKEN B2 METADATA: intake {rid} is Stored but bucket/path is incomplete")
        if row.get("status") == "Processing Failed":
            issues.append(f"INGESTION FAILED: intake {rid} ({row.get('file_name') or 'file'})")

    # Stage 2: B2 -> document record / processor.
    for row in intake:
        rid = str(row.get("id"))
        if row.get("storage_status") != "Stored":
            continue
        age = age_minutes(row.get("received_at"), now)
        linked_doc = None
        if row.get("document_id"):
            linked_doc = next((d for d in docs if str(d.get("id")) == str(row["document_id"]) and is_canonical_telegram_document(d)), None)
        if not linked_doc:
            linked_doc = docs_by_source.get(rid)
            if linked_doc and not is_canonical_telegram_document(linked_doc):
                linked_doc = None
        if not linked_doc and row.get("telegram_message_id") is not None:
            linked_doc = docs_by_source.get(str(row["telegram_message_id"]))
            if linked_doc and not is_canonical_telegram_document(linked_doc):
                linked_doc = None
        if not linked_doc and age is not None and age > STORED_TO_DOCUMENT_MINUTES:
            issues.append(
                f"BROKEN B2→PROCESSOR: intake {rid} has Stored B2 data for {age:.1f}m but no canonical Telegram document record"
            )

    # Stage 3: processor/OCR health for the canonical Telegram pipeline only.
    for row in docs:
        if not is_canonical_telegram_document(row):
            continue
        did = str(row.get("id"))
        status = row.get("processing_status")
        age = age_minutes(row.get("updated_at") or row.get("received_at"), now)
        if status == "Processing" and age is not None and age > PROCESSING_STALE_MINUTES:
            issues.append(f"PROCESSOR STALLED: document {did} has remained Processing for {age:.1f}m")
        if status == "Processing Failed":
            issues.append(f"PROCESSOR FAILED: document {did}")
        if status == "Completed":
            method = str(row.get("extraction_method") or "")
            if "GovDOC Vision" not in method:
                issues.append(f"OCR PROVENANCE BROKEN: document {did} completed without GovDOC Vision provenance")
            if not row.get("full_text_ocr"):
                issues.append(f"OCR RESULT MISSING: document {did} completed without OCR text")
            if not row.get("private_drive_file_id"):
                warnings.append(f"BACKUP PENDING/UNKNOWN: document {did} has no Drive backup id")

    # Stage 4: publication -> delivery for canonical Telegram documents.
    for row in docs:
        if not is_canonical_telegram_document(row) or row.get("publication_status") != "Published":
            continue
        did = str(row.get("id"))
        if not row.get("approved_for_publication") or not row.get("public_file_url"):
            issues.append(f"PUBLICATION INCONSISTENT: document {did} is Published without approval/URL")
        published_age = age_minutes(row.get("updated_at") or row.get("received_at"), now)
        if did not in notified_document_ids and published_age is not None and published_age > PUBLISHED_TO_DELIVERY_MINUTES:
            warnings.append(f"DELIVERY PENDING: document {did} Published for {published_age:.1f}m without Telegram delivery audit")

    # Cross-stage orphan detection using intake PK and Telegram message id.
    for row in intake:
        if not row.get("file_id") or row.get("storage_status") != "Stored":
            continue
        rid = str(row.get("id"))
        linked = docs_by_source.get(rid)
        if linked and is_canonical_telegram_document(linked):
            continue
        if row.get("telegram_message_id") is not None:
            linked = docs_by_source.get(str(row["telegram_message_id"]))
            if linked and is_canonical_telegram_document(linked):
                continue
        age = age_minutes(row.get("received_at"), now)
        if age is not None and age > STORED_TO_DOCUMENT_MINUTES:
            warnings.append(f"LINK DRIFT: intake {rid} is Stored but canonical Telegram document linkage is missing")

    dispatch_runs = github_repository_dispatch_runs()
    dispatch_count_24h = 0
    if dispatch_runs:
        cutoff = now - timedelta(hours=24)
        for run in dispatch_runs:
            created = parse_dt(run.get("created_at"))
            if created and created >= cutoff:
                dispatch_count_24h += 1

    print("=== SCHOOL DOCUMENT PIPELINE WATCHDOG ===")
    print(f"checked_at={now.isoformat()}")
    print(f"watchdog_version=canonical-telegram-scope")
    print(f"intake_24h={len(intake)}")
    print(f"intake_status={dict(intake_counts)}")
    print(f"documents_checked_48h={sum(1 for r in docs if is_canonical_telegram_document(r))}")
    print(f"document_status={dict(doc_counts)}")
    print(f"telegram_delivery_audits_24h={len(audits)}")
    print(f"repository_dispatch_runs_24h={dispatch_count_24h}")
    print(f"thresholds=intake_to_b2:{INTAKE_TO_B2_MINUTES}m,stored_to_document:{STORED_TO_DOCUMENT_MINUTES}m,processing_stale:{PROCESSING_STALE_MINUTES}m,published_to_delivery:{PUBLISHED_TO_DELIVERY_MINUTES}m")
    print(f"issues={len(issues)}")
    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    # Non-zero means an operator should investigate a broken/stalled connection.
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
