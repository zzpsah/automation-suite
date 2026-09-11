#!/usr/bin/env python3
"""Identify safely recoverable School Document Pipeline records.

This utility is intentionally conservative: it reports stale/failed records and
never changes documents automatically. Recovery is performed by the existing
workers on their next eligible run or by an explicit operator action.
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
    cutoff = (now - timedelta(minutes=20)).isoformat()
    rows = get(
        "telegram_intake?select=id,file_name,status,received_at,metadata&received_at=lt."
        + quote(cutoff, safe="")
        + "&status=in.(Received,Stored,Processing Failed,Storage Failed,Storage Partial)&order=received_at.asc&limit=500"
    )
    counts = Counter(str(r.get("status") or "NULL") for r in rows)
    recoverable = []
    for row in rows:
        status = row.get("status")
        metadata = row.get("metadata") or {}
        storage = metadata.get("storage") or {}
        if status in {"Received", "Storage Failed", "Storage Partial"}:
            recoverable.append((row["id"], status, "storage-worker"))
        elif status == "Processing Failed":
            recoverable.append((row["id"], status, "document-processor"))
        elif status == "Stored" and storage.get("b2_status") == "AVAILABLE":
            recoverable.append((row["id"], status, "document-processor"))

    print("=== SCHOOL DOCUMENT PIPELINE RECOVERY ===")
    print(f"checked_at={now.isoformat()}")
    print(f"stale_cutoff={cutoff}")
    print(f"records={len(rows)}")
    print(f"status_counts={dict(counts)}")
    print(f"recoverable={len(recoverable)}")
    for rid, status, worker in recoverable[:100]:
        print(f"RECOVERABLE id={rid} status={status} worker={worker}")
    # This is a diagnostic workflow, not an automatic mutation mechanism.
    return 0


if __name__ == "__main__":
    sys.exit(main())
