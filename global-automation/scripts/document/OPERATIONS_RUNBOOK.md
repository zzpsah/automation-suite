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

## Guarded automatic recovery

The recovery workflow now resolves lifecycle state first and may dispatch **only storage recovery** automatically.

- `RECOVERY_DISPATCH=true` enables dispatch; the default script behavior remains read-only.
- Storage dispatch uses GitHub `repository_dispatch` with event type `document-recovery` and a specific `document_id`.
- The storage worker receives `RECOVERY_DOCUMENT_ID` and processes only that intake record when targeted.
- The storage worker remains retry-safe: existing B2/Drive objects are reused instead of blindly re-uploaded.
- Processing failures are still manual (`RECOVERY_REQUIRED`) and are not auto-reprocessed.
- Publication and Telegram delivery are not auto-triggered by this recovery path; their eligibility/side effects stay with their own workers.
- If the GitHub dispatch fails, the recovery run fails visibly rather than pretending the recovery occurred.

This is deliberate: recovery can delegate a verified storage repair, but it must not manufacture publication eligibility or duplicate downstream side effects.

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
