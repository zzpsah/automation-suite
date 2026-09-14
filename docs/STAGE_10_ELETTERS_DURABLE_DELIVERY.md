# Stage 10 — eLettersBot Durable Delivery

## Objective
Make published-document delivery through eLettersBot durable and recoverable without human intervention.

## Changes
- Added `telegram_publication_deliveries` as the durable per-document/per-chat state table.
- Added an atomic database claim function `claim_telegram_publication_delivery` to prevent concurrent notifier jobs from sending the same delivery at the same time.
- Delivery now tracks `pending → message_sent → sent` and records Telegram message IDs, file hashes, file format, byte size, page count, attempts, timestamps, and the last failure.
- A failed document upload can resume from `message_sent` without sending the metadata message again.
- Legacy successful `document_operations_audit` rows are imported into the durable state table so existing deliveries remain idempotent.
- The targeted notifier now uses the same durable delivery state machine as the scheduled notifier.
- Telegram transient failures retain bounded retries for HTTP 429/5xx and network timeouts.

## Existing delivery contract preserved
The source object is still fetched from Backblaze B2, checksum-verified when metadata provides a checksum, normalized through the existing `telegram_file_delivery` helper, and sent through `eLettersBot`. OCR behavior and recognition features are unchanged.

## Verification
The production Supabase project contains the delivery claim function and the durable table. At Stage 10 activation time the delivery-state table is empty because no synthetic delivery rows are created; real published deliveries populate it organically.

## Remaining honesty boundary
This improves consistency and recovery but cannot provide a distributed exactly-once guarantee across Telegram and PostgreSQL. A process crash immediately after a Telegram API success and before the database checkpoint can still require reconciliation. The durable state machine minimizes that window and prevents normal concurrent/retry duplication.

## Security
The new delivery table has RLS enabled. The claim RPC is `SECURITY DEFINER`, uses `search_path = public`, and execution is restricted to `service_role`.
