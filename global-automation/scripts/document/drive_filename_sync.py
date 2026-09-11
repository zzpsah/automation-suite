#!/usr/bin/env python3
"""Synchronize user-facing document filenames to Google Drive.

Supabase is the metadata source of truth. The B2 object key is intentionally
not changed. Drive file IDs remain stable; only the Drive display name is
updated. Failures are isolated per document so one bad record cannot stop the
batch.
"""
from __future__ import annotations

import os
from urllib.parse import quote

import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
DRIVE_HEADERS = {"Accept": "application/json"}


def db_get(path: str):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def db_patch(rid: str, payload: dict) -> None:
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/documents?id=eq.{quote(str(rid), safe='')}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def access_token() -> str:
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def rename_drive_file(token: str, file_id: str, new_name: str) -> bool:
    r = requests.patch(
        f"https://www.googleapis.com/drive/v3/files/{quote(file_id, safe='')}",
        params={"fields": "id,name"},
        headers={**DRIVE_HEADERS, "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"name": new_name},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("name") == new_name


def main() -> int:
    rows = db_get(
        "documents?select=id,original_filename,display_filename,private_drive_file_id,publication_status&private_drive_file_id=not.is.null&display_filename=not.is.null&order=received_at.asc&limit=200"
    )
    if not rows:
        print("No Drive-backed documents require filename synchronization.")
        return 0

    token = access_token()
    ok = failed = unchanged = 0
    for row in rows:
        rid = row["id"]
        target = row.get("display_filename") or row.get("original_filename")
        file_id = row.get("private_drive_file_id")
        if not target or not file_id:
            continue
        try:
            if rename_drive_file(token, file_id, target):
                db_patch(rid, {"publication_reason": f"Drive filename synchronized: {target}"})
                ok += 1
                print(f"SYNCED {rid}: {target}")
            else:
                failed += 1
                print(f"FAILED {rid}: Drive returned a different filename")
        except Exception as exc:
            failed += 1
            print(f"FAILED {rid}: {exc}")

    print(f"Drive filename sync complete: synced={ok}, failed={failed}, unchanged={unchanged}")
    return 1 if failed and ok == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
