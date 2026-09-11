# Automatic Publication Delivery

## Trigger model

Telegram delivery is intentionally asynchronous and idempotent.

1. `Global Document Publication` publishes an eligible document.
2. Successful completion triggers `Global Document Telegram Notifier` through `workflow_run`.
3. The notifier reads the published document from Supabase.
4. It resolves the originating `telegram_intake` row through `documents.source_message_id`.
5. It reads the private B2 object key from intake metadata.
6. It downloads the PDF bytes from Backblaze B2.
7. It sends a metadata message through the dedicated `@eLettersBot`.
8. It uploads the same PDF bytes with `sendDocument`.
9. It writes `telegram_publication_notification` audit state.

## Reconciliation poll

The notifier also runs every five minutes. This is a safety net for missed workflow events, delayed publication, transient GitHub Actions failures, or documents published by another supported path.

The audit record makes retries idempotent per document and chat. A successful delivery is not sent again to the same recipient.

## Privacy invariant

The Telegram notification does not expose Google Drive or B2 URLs. The PDF is transferred as multipart bytes from the private B2 object to Telegram.

## Failure behavior

- B2 download failure: delivery fails and remains retryable.
- Telegram send failure: delivery fails and remains retryable.
- Audit insert failure after a successful Telegram send can cause a duplicate on a later retry; this is a known residual distributed-systems risk and must be monitored. Do not claim exactly-once delivery.
- Delivery failure does not roll back publication.
- Documents without a valid Telegram intake linkage are skipped safely.

## Current cadence

Immediate trigger: after successful `Global Document Publication` workflow completion.

Reconciliation: every 5 minutes.

This dual-trigger model provides low latency without sacrificing recovery from missed events.
