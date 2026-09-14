# Global Document Pipeline Verification

## Purpose

This document records the implementation-level verification baseline for the School Document Pipeline. This is the **development baseline for 2026-09-14**. All subsequent development and verification work must preserve these invariants unless an explicit, reviewed change supersedes them.

## 2026-09-14 baseline — production behavior observed

The real Telegram acceptance run established the following baseline:

- Fresh intake reaches `telegram_intake` with a durable `progress_message_id`.
- Processing completes through the existing GovDOC Vision/Tesseract path without changing OCR behavior.
- Eligible documents are automatically published.
- Published documents are delivered to `@eLettersBot` through the durable delivery path.
- Delivery state is persisted per `(document_id, chat_id)`.
- A successful delivery is recorded as `sent` with Telegram message IDs and `attempts`.
- Historical successful Telegram publication audit records are reconciled into durable delivery state so old documents are not treated as new work.
- The notifier must use the durable database claim as the sole send gate; a read-then-send `already_sent` check is not an acceptable concurrency control.
- The notifier workflow must not have a second trigger that independently launches delivery for the same publication event. Publication dispatch is the primary event path; scheduled execution is recovery/reconciliation.
- Reconciliation/scheduled runs must be idempotent and must not resend documents whose durable state is already `sent`.
- Existing historical duplicate sends are evidence of the pre-baseline defect and must not be hidden, deleted, or treated as new successful behavior.

### Baseline acceptance rule

For every newly published document and configured recipient, the expected result is:

`1 metadata message + 1 document delivery + 1 durable sent state`

and **no new delivery for unrelated older documents**.

This is the acceptance baseline for all development performed today.

## Verified control flow

```text
@UMVInputBot
    ↓
telegram_intake
    ↓  Storage Worker
Backblaze B2 primary + Google Drive backup
    ↓
telegram_intake = Stored
    ↓  atomic intake claim
Document Processor
    ↓
OCR / metadata / checksum / duplicate checks
    ↓
public.documents = Completed
    ↓  eligibility owned by publication worker
Publication Worker
    ↓
Google Drive public permission + public_file_url
    ↓
publication_status = Published
    ↓
repository_dispatch: document-publication-notify
    ↓
Durable eLetters delivery claim
    ↓
@eLettersBot → configured/private recipients
    ↓
telegram_publication_deliveries.status = sent
    ↓
UMVInputBot progress message reconciliation
```

## Workflow contracts checked

- `global-storage-worker.yml`: scheduled intake processing plus targeted `document-recovery` dispatch; retries reuse existing B2/Drive objects.
- `global-document-processor.yml`: scheduled processing plus targeted `recovery_document_id`; concurrent processors are guarded by the atomic `telegram_intake` claim.
- `global-document-recovery.yml`: read/classify recovery resolver with guarded storage dispatch; processing failures remain manual until bounded job retry semantics exist.
- `global-document-publication.yml`: runs after successful processor completion and on reconciliation schedule; publication eligibility remains worker-owned.
- `global-document-telegram-notifier.yml`: event-driven publication delivery plus scheduled reconciliation; delivery uses `TELEGRAM_OUTPUT_BOT_TOKEN`, verifies `@eLettersBot`, and uses the durable delivery claim as the send gate.
- `global-document-pipeline-health.yml`: read-only consistency checks; structural issues fail the job while asynchronous waiting states remain warnings.
- `global-document-pipeline-tests.yml`: offline compile + smoke-test gate for document scripts.

## P1 invariants

1. `telegram_intake` is the pre-document concurrency lock.
2. `processing_jobs` is document-level and is not used as an intake lock.
3. Recovery classification does not itself perform worker side effects.
4. Storage is B2 primary and Drive backup; private storage URLs are not delivered to Telegram.
5. Publication requires completed processing and explicit worker eligibility checks.
6. Telegram delivery does not republish a document.
7. Durable delivery state is the sole idempotency gate for eLettersBot delivery.
8. Historical successful audit records are considered already delivered and must be reconciled into durable state.
9. Repeated scheduled runs are expected and must remain idempotent.
10. Unrelated publication events must not cancel or replace each other through workflow concurrency.

## Important defect history preserved

During pre-baseline verification, a published document was delivered twice. Investigation showed two independent risks: an unsafe read-then-send delivery pre-check under concurrent notifier runs, and an additional workflow trigger capable of launching a second notifier for the same publication. Older published documents were also resent during reconciliation because legacy successful audit records had not yet been represented in the durable delivery table.

These defects define the reason for the 2026-09-14 baseline. Do not reintroduce any of these patterns.

## Verification fixes applied

The offline CI gate was previously importing `document_processor.py` without its required inert environment variables and without installing its top-level `boto3` dependency. The test workflow now installs `boto3`, and the smoke test supplies non-production placeholder environment values before importing the processor.

The smoke test also exercises the `db_insert()` wrapper introduced for the document creation path, using a fake HTTP response so no external service is contacted.

## Current CI limitation

The GitHub connector may not expose a complete set of Actions status entries for every implementation commit. This document records observed production/database behavior separately from CI status and does **not** infer CI success merely from the existence of a commit.

## Next development rule

All development today starts from this baseline. Changes must preserve exactly-once-like idempotent behavior at the application boundary, with durable reconciliation across notifier retries and schedules. Any deliberate change to the baseline must update this document and the Stage 10 delivery design at the same time.

## Deliberately deferred

Security/RLS hardening outside the already-implemented delivery controls is intentionally separate and must not be inferred as complete from this pipeline verification.
