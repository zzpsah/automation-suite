# UMV File Lifecycle

## Automatic path

```text
RECEIVED
  |
  v
TELEGRAM DOWNLOAD
  |
  v
HASH (SHA-256)
  |
  +-------> R2 PRIMARY
  |
  +-------> B2 BACKUP
  |
  v
VERIFY OBJECTS
  |
  v
SUPABASE METADATA UPDATE
  |
  v
OCR / DOCUMENT PROCESSING
```

## Storage states

Suggested storage status values:

- `PENDING` — intake exists but storage work has not completed.
- `UPLOADING` — upload is in progress.
- `AVAILABLE` — required copies are verified.
- `PARTIAL` — one copy exists and the other needs retry.
- `FAILED` — storage could not be completed after the configured retry policy.
- `REPAIRED` — a previously missing copy was restored from the surviving copy.

## Naming

Objects should use stable generated paths rather than relying on user filenames alone. Recommended pattern:

```text
umv/intake/YYYY/MM/DD/<document-uuid>/<safe-filename>
```

The UUID prevents collisions and the original filename is retained as metadata.

## Integrity

The SHA-256 hash is calculated once from the downloaded bytes and stored in Supabase. Both object copies must represent the same bytes. Object size and checksum/head verification should also be recorded where supported.

## Downloads

The portal should not expose private storage credentials. A server-side endpoint should issue a short-lived signed download URL. If R2 is unavailable, the service can use B2 as the recovery source.
