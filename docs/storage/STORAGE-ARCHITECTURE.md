# UMV Storage Architecture

## Purpose

The UMV Data Input system is designed so that normal file handling requires **no human file-management work**. Telegram is only the input/transport channel; it is not archival storage.

## Target architecture

```text
Telegram (@UMVInputBot)
        |
        v
Supabase Edge Function
        |
        +--------------------+
        |                    |
        v                    v
Cloudflare R2          Supabase PostgreSQL
PRIMARY OBJECT         METADATA / STATUS
STORAGE                     |
        |                    v
        |              OCR / processing
        v
Backblaze B2
INDEPENDENT BACKUP
```

## Responsibilities

| Component | Responsibility |
|---|---|
| Telegram | Receive documents/photos/text from authorized users. Not archival storage. |
| Supabase | Master metadata, processing state, audit trail and search/index data. |
| Cloudflare R2 | Primary private object storage for uploaded files. |
| Backblaze B2 | Independent private backup copy. |
| GitHub Actions | Health checks, reconciliation and operational automation. |

## File lifecycle

1. User sends a document/photo to `@UMVInputBot`.
2. Edge Function records the Telegram intake event in `telegram_intake`.
3. The file is downloaded immediately from Telegram.
4. SHA-256 is calculated from the downloaded bytes.
5. The same bytes are uploaded to R2.
6. The same bytes are uploaded to B2.
7. Storage objects are verified.
8. Supabase is updated with storage locations, hash, size and statuses.
9. Processing/OCR can continue asynchronously.

A file is considered safely archived only when the required storage policy is satisfied. If one provider fails, the record is retained and automatic retry/reconciliation repairs the missing copy.

## Human interaction policy

### Normal operation: none

The operator should only need to send the file through Telegram.

### One-time setup: required

A human must create the R2 and B2 accounts/buckets, perform any email/payment verification required by the providers, and place restricted API credentials into the approved secret stores. Credentials must never be pasted into chat or committed to Git.

### Exception handling

Human intervention is only expected when automation cannot recover a provider/account/configuration failure after retries.

## Security

- R2 and B2 buckets remain private.
- Original files are never made public by default.
- Download access should use short-lived signed URLs.
- R2 credentials must be restricted to the UMV bucket.
- B2 application keys must be restricted to the UMV backup bucket and required operations.
- Supabase service-role credentials remain server-side only.
- Telegram bot tokens remain secret.

## Disaster recovery principle

Supabase is the control plane and index; it is not the only copy of the file. R2 is the primary object store and B2 is an independent provider copy. If R2 becomes unavailable, the system can use the B2 copy and later repair R2. If B2 becomes unavailable, R2 remains the primary copy and backup retries continue.
