#!/usr/bin/env python3
import os
import sys
import boto3
import requests

B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"
B2_BUCKET = os.environ.get("B2_BUCKET_NAME", "Education-Dept-Files")

def require(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing required secret: {name}")
    return value


def check_b2():
    key = require("B2_KEY_ID")
    secret = require("B2_APPLICATION_KEY")
    s3 = boto3.client("s3", endpoint_url=B2_ENDPOINT, aws_access_key_id=key, aws_secret_access_key=secret, region_name="us-east-005")
    s3.head_bucket(Bucket=B2_BUCKET)
    health_key = "_health-check/global-system-health.txt"
    s3.put_object(Bucket=B2_BUCKET, Key=health_key, Body=b"UMV global health check\n", ContentType="text/plain")
    s3.head_object(Bucket=B2_BUCKET, Key=health_key)
    s3.delete_object(Bucket=B2_BUCKET, Key=health_key)
    print("Backblaze B2: GREEN (auth/read/write/delete)")


def check_drive():
    client_id = require("GOOGLE_CLIENT_ID")
    client_secret = require("GOOGLE_CLIENT_SECRET")
    refresh = require("GOOGLE_REFRESH_TOKEN")
    folder = require("GOOGLE_DRIVE_BACKUP_FOLDER_ID")
    token = requests.post("https://oauth2.googleapis.com/token", data={"client_id": client_id, "client_secret": client_secret, "refresh_token": refresh, "grant_type": "refresh_token"}, timeout=30)
    token.raise_for_status()
    access = token.json().get("access_token")
    if not access:
        raise RuntimeError("Google OAuth did not return access token")
    r = requests.get(f"https://www.googleapis.com/drive/v3/files/{folder}", headers={"Authorization": f"Bearer {access}"}, params={"fields": "id,name,mimeType,trashed"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("mimeType") != "application/vnd.google-apps.folder" or data.get("trashed"):
        raise RuntimeError("Configured Google Drive backup folder is invalid or trashed")
    print("Google Drive: GREEN (OAuth/folder access)")


def main():
    check_b2()
    check_drive()
    print("Global storage health: GREEN")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Global storage health: RED — {exc}")
        sys.exit(1)
