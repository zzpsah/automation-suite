# School Document Pipeline — Operations Runbook

## Production flow

Telegram intake → Supabase intake → Backblaze B2 primary → Google Drive backup → SHA-256 verification → internal Tesseract OCR → metadata extraction → duplicate check → contextual filename → publication → public archive.

## Safe operating rules

- `original_filename` is immutable audit data.
- `display_filename` is the human-readable canonical name.
- B2 storage keys are not renamed during metadata/file-name cleanup.
- Supabase metadata is the control-plane source of truth.
- Public publication requires completed processing and safety checks.
- Sensitive and duplicate documents must not be auto-published.
- Failed processing remains auditable; do not delete failure records.
- Global Sarkari OCR remains separate until independently validated.

## Recovery order

1. Check `telegram_intake` status.
2. Check B2 verification and checksum.
3. Check document processing status/error.
4. Reprocess through the controlled operations API when appropriate.
5. Check publication state and public URL.
6. Check Drive filename synchronization.
7. Inspect audit history before manual correction.

## Operational invariants

A healthy published document should have:

- a stable document ID;
- a verified storage object;
- a checksum;
- original and contextual filenames;
- completed processing;
- meaningful subject/authority where available;
- `publication_status=Published`;
- `approved_for_publication=true`;
- a public URL;
- an audit trail.

## Rollback principle

Prefer state transitions (`Unpublished`, `Superseded`, `Archived`) over destructive deletion. Preserve the original file and audit history.

## Testing

Run offline CI before production changes. Use the production test matrix for integration validation. Never publish test fixtures.
