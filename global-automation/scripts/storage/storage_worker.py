#!/usr/bin/env python3
"""Global Telegram intake storage worker.

Pipeline: Telegram -> Backblaze B2 primary -> Google Drive backup -> Supabase metadata.
No third file store is used. Safe to retry: existing B2/Drive objects are reused.
"""
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

import boto3
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APPLICATION_KEY"]
B2_BUCKET = os.environ.get("B2_BUCKET_NAME", "Education-Dept-Files")
B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]
DRIVE_FOLDER_ID = os.environ["GOOGLE_DRIVE_BACKUP_FOLDER_ID"]
RECOVERY_DOCUMENT_ID = os.environ.get("RECOVERY_DOCUMENT_ID", "").strip()

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def db_get(path):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def db_patch(record_id, payload):
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/telegram_intake?id=eq.{quote(str(record_id), safe='')}",
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def telegram(method, payload):
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}", json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method}: {data.get('description', 'unknown error')}")
    return data["result"]


def b2_client():
    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        aws_access_key_id=B2_KEY_ID,
        aws_secret_access_key=B2_APP_KEY,
        region_name="us-east-005",
    )


def b2_object_exists(s3, key):
    """Return True only when the B2 object really exists; stale metadata is not trusted."""
    if not key:
        return False
    try:
        s3.head_object(Bucket=B2_BUCKET, Key=key)
        return True
    except Exception:
        return False


def drive_access_token():
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError("Google OAuth did not return an access token")
    return token


def drive_find_by_sha(token, sha256):
    q = f"'{DRIVE_FOLDER_ID}' in parents and trashed = false and name contains '{sha256}'"
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": q, "fields": "files(id,name,size,md5Checksum)", "pageSize": 10},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("files", [])


def drive_upload(token, name, mime, data):
    boundary = "umv-boundary-" + uuid.uuid4().hex
    metadata = {"name": name, "parents": [DRIVE_FOLDER_ID], "description": "UMV global storage backup"}
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        + json.dumps(metadata, ensure_ascii=False)
        + "\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime or 'application/octet-stream'}\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        params={"uploadType": "multipart", "fields": "id,name,size,webViewLink"},
        data=body,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def process_record(row):
    record_id = row["id"]
    file_id = row.get("file_id")
    if not file_id:
        return False

    metadata = row.get("metadata") or {}
    storage = metadata.get("storage") or {}
    s3 = b2_client()
    b2_key = storage.get("b2_key")
    b2_available = storage.get("b2_status") == "AVAILABLE" and b2_object_exists(s3, b2_key)
    drive_available = storage.get("drive_status") == "AVAILABLE" and bool(storage.get("drive_file_id"))
    if b2_available and drive_available:
        return False

    # If metadata claimed B2 availability but the object is gone, explicitly mark it stale.
    if storage.get("b2_status") == "AVAILABLE" and b2_key and not b2_object_exists(s3, b2_key):
        storage["b2_status"] = "MISSING"
        storage["verified"] = False
        storage["storage_recovery_reason"] = "B2 metadata said AVAILABLE but head_object could not find the object"

    file_info = telegram("getFile", {"file_id": file_id})
    file_path = file_info.get("file_path")
    if not file_path:
        raise RuntimeError("Telegram did not return file_path")

    download = requests.get(
        f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}",
        timeout=120,
    )
    download.raise_for_status()
    data = download.content
    if not data:
        raise RuntimeError("Telegram returned an empty file")

    sha = hashlib.sha256(data).hexdigest()
    safe_name = (row.get("file_name") or "file").replace("/", "_").replace("\\", "_")
    date_path = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    object_key = f"telegram-intake/{date_path}/{record_id}/{safe_name}"

    # The canonical key is deterministic for a record, so a missing/stale object is recreated there.
    if not b2_object_exists(s3, object_key):
        s3.put_object(
            Bucket=B2_BUCKET,
            Key=object_key,
            Body=data,
            ContentType=row.get("mime_type") or "application/octet-stream",
            Metadata={"sha256": sha, "telegram-intake-id": str(record_id)},
        )
    if not b2_object_exists(s3, object_key):
        raise RuntimeError("B2 upload completed without a verifiable object")
    b2_status = "AVAILABLE"

    drive_status = storage.get("drive_status")
    drive_file_id = storage.get("drive_file_id")
    drive_name = f"{sha[:16]}__{safe_name}"
    if drive_status != "AVAILABLE" or not drive_file_id:
        token = drive_access_token()
        existing = drive_find_by_sha(token, sha[:16])
        if existing:
            drive_file_id = existing[0]["id"]
            drive_status = "AVAILABLE"
        else:
            uploaded = drive_upload(token, drive_name, row.get("mime_type") or "application/octet-stream", data)
            drive_file_id = uploaded.get("id")
            if not drive_file_id:
                raise RuntimeError("Google Drive upload returned no file id")
            drive_status = "AVAILABLE"

    storage.update({
        "primary": "Backblaze B2",
        "backup": "Google Drive",
        "b2_status": b2_status,
        "drive_status": drive_status,
        "b2_bucket": B2_BUCKET,
        "b2_key": object_key,
        "drive_file_id": drive_file_id,
        "sha256": sha,
        "size": len(data),
        "verified": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    db_patch(record_id, {"status": "Stored", "metadata": {**metadata, "storage": storage}})
    return True


def main():
    if RECOVERY_DOCUMENT_ID:
        query = (
            "telegram_intake?select=*&id=eq."
            + quote(RECOVERY_DOCUMENT_ID, safe="")
            + "&file_id=not.is.null&limit=1"
        )
    else:
        # Stored rows are included so stale B2 metadata can be reconciled before OCR.
        query = "telegram_intake?select=*&file_id=not.is.null&or=(status.eq.Received,status.eq.Stored,status.eq.Storage%20Failed,status.eq.Storage%20Partial)&order=received_at.asc&limit=10"
    rows = db_get(query)
    processed = 0
    failed = 0
    for row in rows:
        try:
            if process_record(row):
                processed += 1
        except Exception as exc:
            failed += 1
            metadata = row.get("metadata") or {}
            db_patch(
                row["id"],
                {
                    "status": "Storage Failed",
                    "metadata": {
                        **metadata,
                        "storage_error": str(exc)[:500],
                        "storage_error_at": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )
            print(f"Record {row['id']}: storage failed: {exc}")
    print(f"Storage worker complete: processed={processed}, failed={failed}, candidates={len(rows)}, targeted={bool(RECOVERY_DOCUMENT_ID)}")
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
