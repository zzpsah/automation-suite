# Global Storage Layer

Storage component of the **School Document Pipeline**.

## Architecture

```text
Telegram
   |
   v
Supabase telegram_intake
   |
   v
Backblaze B2  <-- PRIMARY
   |
   v
Google Drive  <-- BACKUP
   |
   v
SHA-256 verification
   |
   v
Supabase storage metadata
```

There are exactly **two actual file-storage systems** in the production design:

1. **Backblaze B2 — Primary**
2. **Google Drive — Backup**

Supabase stores metadata/control state; Telegram is only the transport/input channel.

## Configuration

Bucket:

`Education-Dept-Files`

S3 endpoint:

`https://s3.us-east-005.backblazeb2.com`

Google Drive backup folder is supplied through:

`GOOGLE_DRIVE_BACKUP_FOLDER_ID`

## Worker

[`storage_worker.py`](./storage_worker.py)

The worker:

1. Reads pending file records from `telegram_intake`.
2. Downloads the Telegram file.
3. Calculates SHA-256.
4. Writes/reuses the B2 object.
5. Writes/reuses the Google Drive backup.
6. Records both storage references.
7. Marks the record `Stored` only after successful storage.
8. Records size, checksum, statuses and verification timestamp.

Object key format:

```text
telegram-intake/YYYY-MM-DD/<telegram_intake_id>/<safe_filename>
```

## Retry safety

The worker is designed to be rerun safely:

- Existing B2 objects are reused.
- Existing Drive backups are detected by checksum prefix/name.
- Failed records remain in a retryable state.
- No secret is stored in the repository.

## Expected successful metadata

```json
{
  "primary": "Backblaze B2",
  "backup": "Google Drive",
  "b2_status": "AVAILABLE",
  "drive_status": "AVAILABLE",
  "verified": true
}
```

## Workflow

[`global-storage-worker.yml`](../../../.github/workflows/global-storage-worker.yml)

The workflow supports:

- manual execution
- scheduled execution every five minutes
- push-triggered execution for storage worker/workflow changes

The schedule remains the safety net even when no repository changes occur.

## Health monitoring

Storage health checks are included in the global system health workflow:

[`global-system-health.yml`](../../../.github/workflows/global-system-health.yml)

The health layer validates B2 connectivity and object operations plus Google OAuth/Drive configuration.

## Security

The following are GitHub Secrets and must never be committed:

```text
B2_KEY_ID
B2_APPLICATION_KEY
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN
SUPABASE_SERVICE_ROLE_KEY
TELEGRAM_BOT_TOKEN
```

`B2_S3_ENDPOINT` does not need to be secret; production code uses the canonical endpoint directly.

## Related

- [School Document Pipeline](../document/README.md)
- [Automation Suite](../../../../README.md)
- [Backblaze B2](https://www.backblaze.com/cloud-storage)
- [Google Drive API](https://developers.google.com/drive/api)
