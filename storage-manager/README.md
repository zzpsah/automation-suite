# UMV Two-Storage File Manager

Free-first file management for UMV Tetahali.

## Storage policy

1. Backblaze B2 — primary object storage (`Education-Dept-Files`)
2. Google Drive — independent backup (`Education-Dept-Files-Backup`)
3. Supabase — metadata/control plane only; not the archival file store
4. Telegram — transport/input only; never archival storage

No Cloudflare R2 is required.

## Automation goal

A Telegram file should be copied to both storage systems automatically. Normal operation must not require a person to download, rename, copy, verify, or organize the file.

## Required GitHub secrets

- `B2_KEY_ID`
- `B2_APPLICATION_KEY`
- `B2_BUCKET_NAME` = `Education-Dept-Files`
- `B2_S3_ENDPOINT`
- `GOOGLE_DRIVE_FOLDER_ID` = `11o-qvIo-C5UW6yr5hDScrWQ4uOHIw6Pk`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Never commit these values.

## File state

A file is considered fully backed up only after both B2 and Google Drive copies are confirmed and the SHA-256 hash matches the source metadata.

If one side fails, the record remains recoverable and is retried. No destructive cleanup is performed until both copies are confirmed.
