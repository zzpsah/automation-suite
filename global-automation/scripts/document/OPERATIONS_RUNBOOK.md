# School Document Pipeline — Operations Runbook

## Production flow

Telegram intake → Supabase intake → Backblaze B2 primary → Google Drive backup → SHA-256 verification → GovDOC/Tesseract OCR boundary → metadata extraction → duplicate check → contextual filename → autonomous safety-gated publication → eLettersBot delivery.

## Safe operating rules

- `original_filename` is immutable audit data.
- `display_filename` is the human-readable canonical name.
- B2 storage keys are not renamed during metadata/file-name cleanup.
- Supabase metadata is the control-plane source of truth.
- Publication is autonomous after completed processing, but only after machine safety gates pass.
- Sensitive and duplicate documents must not be auto-published.
- OCR text and extraction provenance must be present before publication.
- Failed processing remains auditable; do not delete failure records.
- Global Sarkari OCR remains separate until independently validated.
- Human approval is not required for the normal production flow.

## Recovery order

1. Check `telegram_intake` status.
2. Check B2 verification and checksum.
3. Check document processing status/error.
4. Reprocess through the controlled recovery path when appropriate.
5. Check autonomous publication state and public URL.
6. Check eLettersBot delivery state and file integrity.
7. Inspect audit history before any corrective state change.

## Automatic recovery and publication

The recovery system is designed to repair real pipeline failures without creating fake documents or bypassing provenance.

- Storage recovery reuses existing B2/Drive objects where possible.
- Processing recovery is evidence-driven: verified B2 + existing OCR/document evidence may reconcile stale processing state; genuinely missing source material remains a visible failure.
- Publication is autonomous for `processing_status=Completed` and `publication_status=Unpublished` records that pass machine safety checks.
- Safety checks include verified Drive backup, non-sensitive state, non-duplicate state, usable document, sufficient OCR text, and extraction provenance.
- Low OCR confidence is recorded as metadata; it is not itself a human-approval gate.
- On publication failure, the document remains auditable and is retried by the publication workflow; it is never marked published merely to make health checks green.
- The publication workflow also runs after a successful processor workflow, so completed documents do not depend solely on the five-minute schedule.

## Autonomous progress tracking

One Telegram document uses one progress message wherever possible. The initial message is persisted with chat/message IDs, and later stage updates edit that same message. Progress records the last stage, action (`edited` or fallback), timestamp, and exact failure stage.

Typical stages:

1. Telegram received
2. Supabase intake
3. B2 upload
4. B2 verification
5. Processor start
6. GovDOC OCR
7. Metadata
8. Autonomous publication
9. eLettersBot delivery

## Operational invariants

A healthy published document should have:

- a stable document ID;
- a verified storage object;
- a checksum;
- original and contextual filenames;
- completed processing;
- OCR text and extraction provenance;
- `publication_status=Published`;
- `approved_for_publication=true` as a machine-set compatibility flag;
- a public URL;
- an audit trail.

## Rollback principle

Prefer state transitions (`Unpublished`, `Superseded`, `Archived`) over destructive deletion. Preserve the original file and audit history.

## Testing

Run offline CI before production changes. Use the production test matrix for integration validation. Never publish test fixtures. For live validation, use one real Telegram document at a time and verify every stage from intake through final delivery.
