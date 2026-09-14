# Stage 10 — eLettersBot Durable Delivery

## Objective
Make published-document delivery through eLettersBot durable, recoverable, and idempotent without human intervention.

## 2026-09-14 baseline

Stage 10 is now part of the **2026-09-14 development baseline**. All future work on Telegram publication delivery must preserve these rules:

- One published document + one configured chat must result in one logical delivery.
- The durable database claim is the only idempotency/send gate.
- Historical successful delivery audit records must be reconciled as already sent before scheduled reconciliation is allowed to send anything.
- Scheduled reconciliation is recovery only; it must not turn old published documents into new deliveries.
- The publication event path must not be duplicated by a second workflow trigger for the same publication.
- Existing historical duplicate messages are retained as audit evidence; they are not treated as valid baseline behavior.

## Changes
- Added `telegram_publication_deliveries` as the durable per-document/per-chat state table.
- Added an atomic database claim function `claim_telegram_publication_delivery` to prevent concurrent notifier jobs from sending the same delivery at the same time.
- Delivery now tracks `pending → message_sent → sent` and records Telegram message IDs, file hashes, file format, byte size, page count, attempts, timestamps, and the last failure.
- A failed document upload can resume from `message_sent` without sending the metadata message again.
- Legacy successful `document_operations_audit` rows are imported/reconciled into durable state so existing deliveries remain idempotent.
- The targeted notifier now uses the same durable delivery state machine as the scheduled notifier.
- Telegram transient failures retain bounded retries for HTTP 429/5xx and network timeouts.
- The notifier workflow uses publication `repository_dispatch` as the event-driven path and scheduled execution only as reconciliation; the duplicate `workflow_run` delivery trigger is removed.

## Existing delivery contract preserved
The source object is still fetched from Backblaze B2, checksum-verified when metadata provides a checksum, normalized through the existing `telegram_file_delivery` helper, and sent through `eLettersBot`. OCR behavior and recognition features are unchanged.

## Acceptance baseline

For every new published document and configured recipient:

`1 metadata message + 1 document delivery + 1 durable sent state`

Additionally, the Telegram output must show **no newly generated delivery for unrelated older documents** during reconciliation.

## Verification evidence

A real pre-baseline test exposed duplicate delivery of the same published document and repeated delivery of multiple older documents. Database evidence showed successful sends occurring more than once for the same document/chat across separate runs. This established the need for legacy-audit reconciliation plus a single atomic send gate.

A fresh post-fix document reached `telegram_publication_deliveries.status = sent` with `attempts = 1`, demonstrating the intended durable state transition for a newly published document.

## Remaining honesty boundary
This improves consistency and recovery but cannot provide a distributed exactly-once guarantee across Telegram and PostgreSQL. A process crash immediately after a Telegram API success and before the database checkpoint can still require reconciliation. The durable state machine minimizes this window and prevents normal concurrent/retry duplication. Historical duplicate sends remain historical evidence and are not retroactively undone by the state table.

## Security
The delivery table has RLS enabled. The claim RPC is `SECURITY DEFINER`, uses `search_path = public`, and execution is restricted to `service_role`.

## Development rule
Any change to notifier concurrency, triggers, retry logic, durable state, or historical reconciliation must update this document and `docs/PIPELINE_VERIFICATION.md` together. No new delivery mechanism may bypass the durable claim path.
