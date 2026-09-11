#!/usr/bin/env python3
"""Detect stale document records and optionally dispatch safe recovery.

Default mode is read-only. When RECOVERY_DISPATCH=true, only the STORAGE
recovery action is dispatched automatically. Processing failures remain manual,
and publication/delivery are not invented or auto-triggered here.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[3]
RESOLVER_PATH = ROOT / "global-automation" / "scripts" / "document" / "pipeline_state_resolver.py"
spec = importlib.util.spec_from_file_location("pipeline_state_resolver", RESOLVER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load pipeline_state_resolver.py")
resolver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = resolver
spec.loader.exec_module(resolver)
resolve_state = resolver.resolve_state

BASE = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}


def get(path: str):
    r = requests.get(f"{BASE}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def dispatch_storage(document_id: str, state: str) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPOSITORY are required for recovery dispatch")
    response = requests.post(
        f"https://api.github.com/repos/{repository}/dispatches",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        json={
            "event_type": "document-recovery",
            "client_payload": {
                "worker": "storage",
                "document_id": str(document_id),
                "state": state,
            },
        },
        timeout=30,
    )
    if response.status_code not in (204,):
        raise RuntimeError(f"GitHub recovery dispatch failed: {response.status_code} {response.text[:500]}")


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
    dispatched = 0
    dispatch_enabled = os.environ.get("RECOVERY_DISPATCH", "false").lower() == "true"

    for row in rows:
        doc = docs_by_source.get(str(row.get("id")))
        if doc is None:
            doc = {"id": str(row.get("id")), "processing_status": "", "publication_status": ""}
        state = resolve_state(doc, row)
        state_counts[state.state] += 1
        if state.next_action != "none":
            recoverable.append((row["id"], row.get("status"), state.state, state.next_action, state.reason))
            if dispatch_enabled and state.next_action == "storage":
                dispatch_storage(str(row["id"]), state.state)
                dispatched += 1
                print(f"DISPATCHED id={row['id']} worker=storage state={state.state}")

    print("=== SCHOOL DOCUMENT PIPELINE RECOVERY ===")
    print(f"checked_at={now.isoformat()}")
    print(f"stale_cutoff={cutoff}")
    print(f"records={len(rows)}")
    print(f"status_counts={dict(counts)}")
    print(f"resolved_states={dict(state_counts)}")
    print(f"recoverable={len(recoverable)}")
    print(f"dispatch_enabled={dispatch_enabled}")
    print(f"dispatched={dispatched}")
    for rid, status, state, worker, reason in recoverable[:100]:
        print(f"RECOVERABLE id={rid} status={status} state={state} worker={worker} reason={reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
