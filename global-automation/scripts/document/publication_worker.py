#!/usr/bin/env python3
"""Publish safe, completed Telegram documents to the public school archive."""
import os
import sys
from datetime import datetime, timezone
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
DRIVE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
DRIVE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
DRIVE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def db_get(path):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def db_patch(rid, payload):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/documents?id=eq.{rid}", headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"}, json=payload, timeout=30)
    r.raise_for_status()


def drive_access_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": DRIVE_CLIENT_ID, "client_secret": DRIVE_CLIENT_SECRET,
        "refresh_token": DRIVE_REFRESH_TOKEN, "grant_type": "refresh_token"
    }, timeout=30)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError("Google OAuth did not return an access token")
    return token


def make_public(token, file_id):
    r = requests.post(
        f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
        params={"sendNotificationEmail": "false", "supportsAllDrives": "true"},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"type": "anyone", "role": "reader"}, timeout=30,
    )
    if r.status_code not in (200, 201, 409):
        raise RuntimeError(f"Google Drive permission failed {r.status_code}: {r.text[:500]}")


def eligible(row):
    # Date extraction is useful metadata but must not block publication when the
    # original document contains no reliably machine-readable date.
    return (
        row.get("processing_status") == "Completed"
        and row.get("publication_status") in (None, "Unpublished")
        and bool(row.get("private_drive_file_id"))
        and not bool(row.get("sensitive"))
        and not bool(row.get("duplicate"))
        and bool(row.get("useful", True))
        and row.get("extraction_confidence") in ("HIGH", "MEDIUM")
        and bool(row.get("subject"))
    )


def main():
    rows = db_get("documents?select=id,processing_status,publication_status,private_drive_file_id,sensitive,duplicate,useful,extraction_confidence,subject,public_file_url,public_revision&processing_status=eq.Completed&publication_status=eq.Unpublished&limit=25")
    if not rows:
        print("Publication worker: no pending documents")
        return 0
    token = None
    published = skipped = failed = 0
    for row in rows:
        rid = row["id"]
        if not eligible(row):
            skipped += 1
            continue
        try:
            token = token or drive_access_token()
            file_id = row["private_drive_file_id"]
            make_public(token, file_id)
            public_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            db_patch(rid, {
                "public_file_url": public_url,
                "approved_for_publication": True,
                "publication_status": "Published",
                "publication_reason": "Automatically published: completed, non-sensitive, non-duplicate document with sufficient extracted metadata and verified Drive backup.",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "public_revision": int(row.get("public_revision") or 0) + 1,
            })
            published += 1
            print(f"Published {rid} -> Google Drive public URL")
        except Exception as exc:
            failed += 1
            try:
                db_patch(rid, {"publication_reason": f"Publication failed: {str(exc)[:900]}"})
            except Exception as patch_exc:
                print(f"Record {rid}: publication failure and status patch failure: {patch_exc}")
            print(f"Record {rid}: publication failed: {exc}")
    print(f"Publication worker complete: published={published}, skipped={skipped}, failed={failed}, candidates={len(rows)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
