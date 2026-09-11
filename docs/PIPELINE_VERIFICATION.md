# Global Document Pipeline Verification

## Purpose

This document records the implementation-level verification baseline for the School Document Pipeline. It is intended to make continuation safe when work resumes in a later conversation.

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
Telegram Notifier
    ↓
@eLettersBot → configured/private recipients
```

## Workflow contracts checked

- `global-storage-worker.yml`: scheduled intake processing plus `document-recovery` targeted dispatch; retries reuse existing B2/Drive objects.
- `global-document-processor.yml`: scheduled processing plus targeted `recovery_document_id`; concurrent processors are guarded by the atomic `telegram_intake` claim.
- `global-document-recovery.yml`: read/classify recovery resolver with guarded storage dispatch; processing failures remain manual until bounded job retry semantics exist.
- `global-document-publication.yml`: runs after successful processor completion and on reconciliation schedule; publication eligibility remains worker-owned.
- `global-document-telegram-notifier.yml`: runs after successful publication and on reconciliation schedule; delivery uses `TELEGRAM_OUTPUT_BOT_TOKEN` and verifies `@eLettersBot` before sending.
- `global-document-pipeline-health.yml`: read-only consistency checks; structural issues fail the job while asynchronous waiting states remain warnings.
- `global-document-pipeline-tests.yml`: offline compile + smoke-test gate for document scripts.

## P1 invariants

1. `telegram_intake` is the pre-document concurrency lock.
2. `processing_jobs` is document-level and is not used as an intake lock.
3. Recovery classification does not itself perform worker side effects.
4. Storage is B2 primary and Drive backup; private storage URLs are not delivered to Telegram.
5. Publication requires completed processing and explicit worker eligibility checks.
6. Telegram delivery does not republish a document.
7. Repeated scheduled runs are expected and must remain idempotent.

## Verification fixes applied

The offline CI gate was previously importing `document_processor.py` without its required inert environment variables and without installing its top-level `boto3` dependency. The test workflow now installs `boto3`, and the smoke test supplies non-production placeholder environment values before importing the processor.

The smoke test also exercises the `db_insert()` wrapper introduced for the document creation path, using a fake HTTP response so no external service is contacted.

## Current CI limitation

The GitHub connector currently reports no commit status entries for the latest implementation commits, so this document does **not** claim that GitHub Actions has completed successfully. The next verification point is the actual Actions run for the latest `global-document-pipeline-tests.yml` change.

## Next meaningful upgrade

After the offline CI gate is green, implement the document-level `processing_jobs` lifecycle deliberately: deterministic job identity, an appropriate uniqueness constraint, atomic job claiming, bounded retry/backoff, and auditability. Do not enable automatic processing retries before those controls exist.

## Deliberately deferred

Security/RLS hardening is intentionally outside this implementation pass and must not be inferred as complete from the pipeline verification above.
