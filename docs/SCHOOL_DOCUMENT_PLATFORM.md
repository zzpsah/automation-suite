# School Document Platform — Production Contract

## Scope
This document defines the production document path owned by the core automation layer. OCR/language-pack/model improvement remains a separate GovDoc Vision concern.

## Canonical flow

```text
Input
  -> Telegram intake (@UMVInputBot)
  -> Supabase telegram_intake
  -> B2 primary storage
  -> Google Drive backup
  -> Processing / OCR consumer
  -> Supabase documents metadata
  -> Publication worker
  -> Public school archive / portal
  -> Telegram delivery (@eLettersBot)
  -> Audit + health/recovery
```

## Stage ownership

| Stage | System | Contract |
|---|---|---|
| Input | UMVInputBot + Telegram gateway | Accept text, document and photo input; create durable intake record |
| Control plane | Supabase | Metadata, state, provenance, audit; never the file store |
| Primary storage | Backblaze B2 | Private source file; stable object key; checksum |
| Backup | Google Drive | Durable backup; Drive ID retained in metadata |
| Processing | GitHub Actions worker | Verify B2, extract text/metadata, create document record |
| Publication | Publication worker | Publish only completed, non-sensitive, non-duplicate, useful records with sufficient metadata and backup |
| Portal | School portal/archive | Read published metadata and public document representation |
| Delivery | eLettersBot | Send formatted metadata + actual PDF; never expose B2/Drive storage URLs |
| Recovery | Recovery worker + health checks | Retry safe transient/stuck stages; never destructively delete records |

## State invariants

1. A source file must have a durable `telegram_intake` record before processing.
2. A processed document must retain source provenance through `source_message_id`.
3. B2 is the primary file store; Google Drive is the backup.
4. Storage keys are stable even when the user-facing filename changes.
5. Publication is non-destructive and auditable.
6. Telegram delivery is asynchronous and idempotent; missing delivery audit is retryable, not a publication rollback.
7. Telegram delivery must use the dedicated output bot and actual PDF bytes, not a storage URL.
8. OCR/language knowledge is not copied into consuming applications.
9. Processing, publication and delivery failures must remain visible to health/recovery tooling.
10. Existing Apps Script remains outside this global automation contract and is not modified by the core workflow.

## Automatic operation

The production workers run on schedules and workflow dependencies. A normal new document therefore progresses without manual approval:

`input -> stored -> processed -> published -> delivered`

Manual review is reserved for genuine processing failures or controlled document operations; it is not a mandatory approval gate for every successful document.

## Security

- Never put service-role keys, bot tokens, B2 keys or OAuth refresh tokens in source files.
- Public portal URLs and Telegram delivery are separate concerns.
- Delivery messages must not expose storage-provider URLs.
- Preserve original source evidence and provenance; derived metadata may be corrected without deleting the original record.

## Operational checks

`pipeline_health.py` is read-only. It checks cross-stage consistency, storage state and recent Telegram publication-delivery audits. Normal asynchronous waiting is a warning; structural inconsistencies fail the health check.

## GovDoc Vision boundary

The reusable OCR platform is consumed by this pipeline but is not owned by it. Its OCR engine, language packs, document intelligence and training/regression system remain independently versioned. This pipeline should consume the stable OCR service contract rather than duplicating OCR rules.
