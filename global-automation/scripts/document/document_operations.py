#!/usr/bin/env python3
"""Safe, explicit document operations for the School Document Pipeline."""
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
    response = requests.request(method, f"{BASE}/rest/v1/{path}", headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json() if response.text else []


def get_document(document_id: str) -> dict:
    did = quote(document_id, safe="")
    rows = request("GET", f"documents?select=id,processing_status,publication_status,document_version,canonical_document_id,supersedes_document_id,subject&id=eq.{did}")
    if not rows:
        raise RuntimeError(f"document not found: {document_id}")
    return rows[0]


def audit(document_id: str, operation: str, details: dict, before: dict | None = None, after: dict | None = None):
    request("POST", "document_operations_audit", {
        "document_id": document_id,
        "operation": operation,
        "actor_type": "operator",
        "from_status": before or {},
        "to_status": after or {},
        "details": details,
    })


def request_reprocess(document_id: str, reason: str):
    before = get_document(document_id)
    now = datetime.now(timezone.utc).isoformat()
    did = quote(document_id, safe="")
    after = request("PATCH", f"documents?id=eq.{did}", {
        "reprocess_requested_at": now,
        "reprocess_reason": reason,
        "updated_at": now,
    })[0]
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
    new_key = quote(new_id, safe="")
    updated_new = request("PATCH", f"documents?id=eq.{new_key}", {
        "supersedes_document_id": old_id,
        "document_version": max(int(old.get("document_version") or 1) + 1, int(new.get("document_version") or 1)),
        "canonical_document_id": old.get("canonical_document_id") or old_id,
        "updated_at": now,
    })[0]
    old_key = quote(old_id, safe="")
    updated_old = request("PATCH", f"documents?id=eq.{old_key}", {
        "publication_status": "Superseded",
        "unpublished_at": now,
        "updated_at": now,
    })[0]
    audit(old_id, "superseded", {"replacement_document_id": new_id}, old, updated_old)
    audit(new_id, "replacement_for", {"superseded_document_id": old_id}, new, updated_new)
    return {"superseded": updated_old, "replacement": updated_new}


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
