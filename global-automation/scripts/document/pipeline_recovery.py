#!/usr/bin/env python3
"""Identify safely recoverable School Document Pipeline records.

This utility is intentionally conservative: it reports stale/failed records and
never changes documents automatically. The lifecycle resolver classifies the
observed evidence; existing workers remain responsible for mutations.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[3]
RESOLVER_PATH = ROOT / "global-automation" / "scripts" / "document" / "pipeline_state_resolver.py"
spec = importlib.util.spec_from_file_location("pipeline_state_resolver", RESOLVER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load pipeline_state_resolver.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)
resolve_state = resolver.resolve_state

BASE = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}


def get(path: str):
    r = requests.get(f"{BASE}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


# Import requests after resolver loading so this module remains easy to load in tests.
import requests


def main() -> int:
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(minutes=20)).isoformat()
    rows = get(
        "telegram_intake?select=id,file_name,status,received_at,metadata&received_at=lt."
        + quote(cutoff, safe="")
        + "&status=in.(Received,Stored,Processing Failed,Storage Failed,Storage Partial)&order=received_at.asc&limit=500"
    )
    docs = get(
        "documents?select=id,source_message_id,processing_status,publication_status,approved_for_publication,delivery_status&limit=500"
    )
    counts = Counter(str(r.get("status") or "NULL") for r in rows)
    docs_by_source = {str(d.get("source_message_id")): d for d in docs if d.get("source_message_id")}
    recoverable = []
    state_counts = Counter()

    for row in rows:
        doc = docs_by_source.get(str(row.get("id")))
        if doc is None:
            doc = {"id": str(row.get("id")), "processing_status": "", "publication_status": ""}
        state = resolve_state(doc, row)
        state_counts[state.state] += 1
        if state.next_action != "none":
            recoverable.append((row["id"], row.get("status"), state.state, state.next_action, state.reason))

    print("=== SCHOOL DOCUMENT PIPELINE RECOVERY ===")
    print(f"checked_at={now.isoformat()}")
    print(f"stale_cutoff={cutoff}")
    print(f"records={len(rows)}")
    print(f"status_counts={dict(counts)}")
    print(f"resolved_states={dict(state_counts)}")
    print(f"recoverable={len(recoverable)}")
    for rid, status, state, worker, reason in recoverable[:100]:
        print(f"RECOVERABLE id={rid} status={status} state={state} worker={worker} reason={reason}")
    # Diagnostic only: resolver is read-only and workers own side effects.
    return 0


if __name__ == "__main__":
    sys.exit(main())
