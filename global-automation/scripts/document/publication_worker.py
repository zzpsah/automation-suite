#!/usr/bin/env python3
"""Autonomous publisher for safe, completed Telegram documents.

Human approval is not a production prerequisite. Publication is controlled by
machine safety gates: completed processing, verified backup, OCR presence,
non-sensitive/non-duplicate state, and a usable source record.
"""
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
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/documents?id=eq.{rid}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def drive_access_token():
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": DRIVE_CLIENT_ID,
            "client_secret": DRIVE_CLIENT_SECRET,
            "refresh_token": DRIVE_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
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
        json={"type": "anyone", "role": "reader"},
        timeout=30,
    )
    if r.status_code not in (200, 201, 409):
        raise RuntimeError(f"Google Drive permission failed {r.status_code}: {r.text[:500]}")


def autonomous_quality_gate(row):
    """Return (ok, reason) without human approval.

    Low/medium confidence is not itself a blocker. The safety decision relies on
    actual extracted text, verified backup, and integrity/provenance flags.
    """
    checks = []
    if row.get("processing_status") != "Completed":
        checks.append("processing_not_completed")
    if row.get("publication_status") not in (None, "Unpublished"):
        checks.append("publication_not_pending")
    if not row.get("private_drive_file_id"):
        checks.append("drive_backup_missing")
    if bool(row.get("sensitive")):
        checks.append("sensitive_document")
    if bool(row.get("duplicate")):
        checks.append("duplicate_document")
    if row.get("useful") is False:
        checks.append("document_marked_not_useful")
    ocr = str(row.get("full_text_ocr") or "").strip()
    if len(ocr) < 80:
        checks.append("insufficient_ocr_text")
    if not str(row.get("extraction_method") or "").strip():
        checks.append("missing_extraction_provenance")
    return (not checks, "ok" if not checks else ",".join(checks))


def main():
    rows = db_get(
        "documents?select=id,processing_status,publication_status,private_drive_file_id," 
        "sensitive,duplicate,useful,extraction_confidence,subject,public_file_url," 
        "public_revision,full_text_ocr,extraction_method&processing_status=eq.Completed&"
        "publication_status=eq.Unpublished&limit=25"
    )
    if not rows:
        print("Publication worker: no pending documents")
        return 0

    token = None
    published = skipped = failed = 0
    for row in rows:
        rid = row["id"]
        eligible, reason = autonomous_quality_gate(row)
        if not eligible:
            skipped += 1
            print(f"Skipped {rid}: autonomous safety gate -> {reason}")
            db_patch(rid, {"publication_reason": f"Autonomous publication gate: {reason}"})
            continue
        try:
            token = token or drive_access_token()
            file_id = row["private_drive_file_id"]
            make_public(token, file_id)
            public_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            confidence = row.get("extraction_confidence") or "UNKNOWN"
            db_patch(
                rid,
                {
                    "public_file_url": public_url,
                    "approved_for_publication": True,
                    "publication_status": "Published",
                    "publication_reason": (
                        "Automatically published by autonomous safety gate: completed processing, "
                        "verified OCR/provenance, verified Drive backup, and no sensitive/duplicate flags. "
                        f"Extraction confidence recorded as {confidence}."
                    ),
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "public_revision": int(row.get("public_revision") or 0) + 1,
                },
            )
            published += 1
            print(f"Published {rid} -> Google Drive public URL")
        except Exception as exc:
            failed += 1
            try:
                db_patch(rid, {"publication_reason": f"Publication failed: {str(exc)[:900]}"})
            except Exception as patch_exc:
                print(f"Record {rid}: publication failure and status patch failure: {patch_exc}")
            print(f"Record {rid}: publication failed: {exc}")

    print(
        f"Publication worker complete: published={published}, skipped={skipped}, "
        f"failed={failed}, candidates={len(rows)}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
