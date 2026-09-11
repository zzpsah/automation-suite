#!/usr/bin/env python3
"""Read-only health checks for the School Document Pipeline.

Checks recent intake/storage/processing/publication/delivery state and detects
records that are inconsistent across stages. It never mutates production data.
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


def get(path: str):
    r = requests.get(f"{BASE}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> int:
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=24)).isoformat()
    intake = get(f"telegram_intake?select=id,file_name,status,received_at,metadata&received_at=gte.{quote(cutoff, safe='')}&order=received_at.desc&limit=200")
    docs = get("documents?select=id,source_message_id,original_filename,display_filename,file_checksum,private_drive_file_id,processing_status,publication_status,approved_for_publication,public_file_url,subject,issuing_authority,received_at&order=received_at.desc&limit=200")
    audits = get("document_operations_audit?select=document_id,operation,details,created_at&operation=eq.telegram_publication_notification&created_at=gte." + quote(cutoff, safe="") + "&limit=1000")

    intake_counts = Counter(str(r.get("status") or "NULL") for r in intake)
    doc_counts = Counter(f"{r.get('processing_status') or 'NULL'}/{r.get('publication_status') or 'NULL'}" for r in docs)
    intake_by_id = {str(r["id"]): r for r in intake if r.get("id")}
    doc_message_ids = {str(r["source_message_id"]) for r in docs if r.get("source_message_id")}
    notified_pairs = {
        (str(a.get("document_id")), str((a.get("details") or {}).get("chat_id")))
        for a in audits
        if a.get("document_id") and (a.get("details") or {}).get("chat_id")
    }

    issues: list[str] = []
    warnings: list[str] = []
    for row in docs:
        did = row.get("id")
        source_id = str(row.get("source_message_id") or "")
        intake_row = intake_by_id.get(source_id)
        if row.get("processing_status") == "Completed" and not row.get("subject"):
            issues.append(f"document {did}: Completed without subject")
        if row.get("processing_status") == "Completed" and not row.get("private_drive_file_id"):
            issues.append(f"document {did}: Completed without Drive backup id")
        if intake_row:
            storage = (intake_row.get("metadata") or {}).get("storage") or {}
            if row.get("processing_status") == "Completed" and storage.get("b2_status") not in (None, "AVAILABLE"):
                issues.append(f"document {did}: Completed but B2 storage status is {storage.get('b2_status')}")
            if row.get("processing_status") == "Completed" and storage.get("drive_status") not in (None, "AVAILABLE"):
                issues.append(f"document {did}: Completed but Drive backup status is {storage.get('drive_status')}")
        elif source_id:
            warnings.append(f"document {did}: source intake record not found in recent 24h window")
        if row.get("publication_status") == "Published":
            if not row.get("approved_for_publication") or not row.get("public_file_url"):
                issues.append(f"document {did}: Published but public approval/URL missing")
            # Delivery is asynchronous. Missing audit is a delivery-pending signal,
            # not a publication failure, so the notifier can retry safely.
            if not any(pair[0] == str(did) for pair in notified_pairs):
                warnings.append(f"document {did}: Published but no Telegram delivery audit in last 24h")

    orphan_intake = [r for r in intake if r.get("status") in {"Stored", "Processing", "Received"} and str(r.get("id")) not in doc_message_ids]
    for row in orphan_intake[:20]:
        warnings.append(f"intake {row.get('id')}: {row.get('status')} with no document record yet")

    print("=== SCHOOL DOCUMENT PIPELINE HEALTH ===")
    print(f"checked_at={now.isoformat()}")
    print(f"intake_24h={len(intake)}")
    print(f"intake_status={dict(intake_counts)}")
    print(f"documents_checked={len(docs)}")
    print(f"document_status={dict(doc_counts)}")
    print(f"telegram_delivery_audits_24h={len(audits)}")
    print(f"issues={len(issues)}")
    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    # Waiting between asynchronous stages is normal. Only structural failures
    # should fail CI; warnings remain visible for operators and retry workers.
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
