# End-to-End Document Pipeline Reconciliation

## Scope

Reconciliation observes the lifecycle from intake/storage through processing, publication, and Telegram delivery. It does not replace workers and does not perform destructive actions.

## P1 control-plane boundary

The pipeline has two different concurrency/control mechanisms and they must not be mixed:

### 1. Intake claim — before a document exists

`telegram_intake` is the concurrency guard for the pre-document stage.

- Eligible states: `Stored` and `Processing Failed`.
- The processor claims a row with one conditional update to `Processing`.
- A concurrent processor that loses the race receives no representation and skips the row.
- This prevents the same intake record from entering OCR twice at the same time.

This is intentionally an **intake-level lock**, not a `processing_jobs` lock.

### 2. Processing job — after a document exists

`processing_jobs` is a document-level lifecycle record.

- `document_id` is required, so it cannot safely be used to lock an intake record before document creation.
- Job fields provide the future control surface for reprocessing: `job_type`, `status`, `attempt_count`, `next_attempt_at`, `last_error`, and `locked_at`.
- The current intake processor therefore uses the atomic intake claim for initial OCR and does not pretend that `processing_jobs` is a pre-document lock.
- Job creation/claim semantics must be made idempotent before automated reprocessing is enabled.

This separation avoids creating a second concurrency model that can disagree with the actual intake state.

## Recovery routing

- `Processing Failed`, `Needs Manual Review`, `Action Required` → processing/manual-review handling.
- Storage error states → storage recovery.
- Completed but unpublished items → publication worker evaluates eligibility.
- Published + approved items → delivery reconciliation.
- Otherwise → no automatic recovery action.

## Safety rules

1. Never delete a document to recover it.
2. Never republish solely because a delivery failed.
3. Never expose private B2/Drive URLs to Telegram recipients.
4. Do not invent publication eligibility during reconciliation.
5. Run repeatedly without creating a second logical recovery state.
6. Do not use `processing_jobs` as a pre-document lock.
7. Do not enable automatic processing retry merely because a processing failure exists; failed processing remains a bounded/manual recovery path until job retry semantics are explicitly implemented.

## Operational model

`observe → classify → delegate → worker acts → audit → observe again`

The system therefore becomes self-healing through bounded, stage-specific workers while preserving Supabase as the control-plane source of truth.

## P1 implementation note

The processor's intake claim is the authoritative concurrency boundary for the initial `Stored → Processing → Processed` path. `processing_jobs` remains reserved for document-level processing/reprocessing control. The next implementation step is to add deterministic job creation and atomic job claiming only after a document identifier exists.
