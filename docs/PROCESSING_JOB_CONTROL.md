# Processing Job Control

## Purpose

This document defines the boundary between Telegram intake claiming and document-level processing jobs.

## Two different controls

### 1. Intake claim

`telegram_intake.status` is the concurrency guard used before a document record exists.

Eligible states are claimed atomically:

`Stored` / `Processing Failed` → `Processing`

Only the worker that successfully receives the conditional update owns that intake record for the current processing attempt. A second concurrent worker must skip it.

### 2. Processing job

`processing_jobs` is a document-level lifecycle record. It requires `document_id`, so it must not be used as the lock for the initial Telegram-to-document conversion.

The job table is reserved for processing/reprocessing work after the document identity exists.

## Job states

The database contract currently allows:

- `Queued` — work requested but not started.
- `Processing` — worker has claimed the job.
- `Completed` — processing finished successfully.
- `Failed` — worker stopped after an error and the job is eligible for explicit retry policy.
- `Manual Review` — automation must stop and a human decision is required.

## Attempt accounting

`attempt_count` records processing attempts. It must never become negative.

`locked_at` records when a job was claimed. `last_error` records the latest failure reason. `next_attempt_at` is the scheduling boundary for a future retry policy.

The presence of these fields does not by itself authorize automatic retries. Retry policy remains a worker/control-plane decision.

## Current safety boundary

Automatic reconciliation may route a processing failure to processing/manual-review handling, but it must not blindly retry every failed processing job. In particular, `Processing Failed` intake records remain manual until a bounded retry contract is deliberately implemented and tested.

## Required invariants

1. Intake claiming and document job claiming remain separate mechanisms.
2. A job cannot be created as the initial pre-document lock because `document_id` is required.
3. Workers own processing side effects; reconciliation only observes, classifies, and delegates.
4. A failed processing attempt must preserve its error evidence.
5. Re-running reconciliation must not create duplicate logical work.
6. No delete operation is used to recover a processing job.
7. Publication eligibility is not inferred from processing-job success.

## Lifecycle

```text
Telegram intake
      ↓
Stored
      ↓
atomic intake claim
      ↓
Processing
      ↓
create/update document
      ↓
document-level processing job
      ↓
Queued → Processing → Completed
                  ↘ Failed → Manual Review / bounded retry
```

## Implementation order

The safe implementation sequence is:

1. Keep the existing atomic intake claim as the pre-document concurrency guard.
2. Fix the processor's database insert helper so document creation is explicit and testable.
3. Record document-level processing job state after the document identity exists.
4. Add an atomic job claim only when a unique job identity/constraint is available.
5. Add bounded retry scheduling only after failure semantics and observability are tested.

Security/RLS is intentionally outside this increment and will be handled separately.
