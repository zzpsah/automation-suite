#!/usr/bin/env python3
"""Read-only health checks for the School Document Pipeline.

Checks recent intake/storage/processing/publication state and detects records
that are inconsistent across stages. It never mutates production data.
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

    intake_counts = Counter(str(r.get("status") or "NULL") for r in intake)
    doc_counts = Counter(f"{r.get('processing_status') or 'NULL'}/{r.get('publication_status') or 'NULL'}" for r in docs)
    intake_ids = {str(r["id"]) for r in intake if r.get("id")}
    doc_message_ids = {str(r["source_message_id"]) for r in docs if r.get("source_message_id")}

    issues: list[str] = []
    for row in docs:
        did = row.get("id")
        if row.get("processing_status") == "Completed" and not row.get("subject"):
            issues.append(f"document {did}: Completed without subject")
        if row.get("publication_status") == "Published" and (not row.get("approved_for_publication") or not row.get("public_file_url")):
            issues.append(f"document {did}: Published but public approval/URL missing")
        if row.get("processing_status") == "Completed" and not row.get("private_drive_file_id"):
            issues.append(f"document {did}: Completed without Drive backup id")
        if row.get("source_message_id") and str(row["source_message_id"]) not in intake_ids:
            issues.append(f"document {did}: source intake record not found in recent 24h window")

    orphan_intake = [r for r in intake if r.get("status") in {"Stored", "Processing", "Received"} and str(r.get("id")) not in doc_message_ids]
    for row in orphan_intake[:20]:
        issues.append(f"intake {row.get('id')}: {row.get('status')} with no document record yet")

    print("=== SCHOOL DOCUMENT PIPELINE HEALTH ===")
    print(f"checked_at={now.isoformat()}")
    print(f"intake_24h={len(intake)}")
    print(f"intake_status={dict(intake_counts)}")
    print(f"documents_checked={len(docs)}")
    print(f"document_status={dict(doc_counts)}")
    print(f"issues={len(issues)}")
    for issue in issues:
        print(f"ISSUE: {issue}")

    # Existing Received/Stored records may legitimately be waiting for the next
    # five-minute worker cycle, so only structural inconsistencies fail the job.
    hard = [x for x in issues if "Published but" in x or "Completed without" in x]
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
