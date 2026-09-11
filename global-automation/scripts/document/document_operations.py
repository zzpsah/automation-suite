#!/usr/bin/env python3
"""Safe document operations for the School Document Pipeline.

This module exposes explicit, auditable operations rather than automatic mutations:
request_reprocess and supersede. It is designed for an admin/operator workflow.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from urllib.parse import quote

import requests

BASE = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}


def request(method: str, path: str, payload: dict | None = None):
    r = requests.request(method, f"{BASE}/rest/v1/{path}", headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json() if r.text else []


def get_document(document_id: str) -> dict:
    rows = request("GET", f"documents?select=id,processing_status,publication_status,document_version,canonical_document_id,supersedes_document_id,subject& id=eq.{quote(document_id, safe='')}")
    if not rows:
        raise RuntimeError(f"document not found: {document_id}")
    return rows[0]


def audit(document_id: str, operation: str, details: dict, before: dict | None = None, after: dict | None = None):
    request("POST", "document_operations_audit", {"document_id": document_id, "operation": operation, "actor_type": "operator", "from_status": before or {}, "to_status": after or {}, "details": details})


def request_reprocess(document_id: str, reason: str):
    before = get_document(document_id)
    now = datetime.now(timezone.utc).isoformat()
    after = request("PATCH", f"documents?id=eq.{quote(document_id, safe='')}", {"reprocess_requested_at": now, "reprocess_reason": reason, "updated_at": now})[0]
    audit(document_id, "reprocess_requested", {"reason": reason}, before, after)
    return after


def supersede(old_id: str, new_id: str):
    old = get_document(old_id)
    new = get_document(new_id)
    if old_id == new_id:
        raise ValueError("a document cannot supersede itself")
    if old.get("publication_status") != "Published":
        raise ValueError("only a published document can be superseded")
    if new.get("publication_status") != "Published":
        raise ValueError("replacement document must be published before superseding")
    now = datetime.now(timezone.utc).isoformat()
    updated = request("PATCH", f"documents?id=eq.{quote(old_id, safe='')}", {"publication_status": "Superseded", "supersedes_document_id": new_id, "unpublished_at": now, "updated_at": now})[0]
    audit(old_id, "superseded", {"replacement_document_id": new_id}, old, updated)
    audit(new_id, "replacement_for", {"superseded_document_id": old_id}, new, new)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    rp = sub.add_parser("reprocess")
    rp.add_argument("document_id")
    rp.add_argument("reason")
    sp = sub.add_parser("supersede")
    sp.add_argument("old_document_id")
    sp.add_argument("new_document_id")
    args = parser.parse_args()
    if args.command == "reprocess":
        print(request_reprocess(args.document_id, args.reason))
    else:
        print(supersede(args.old_document_id, args.new_document_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
