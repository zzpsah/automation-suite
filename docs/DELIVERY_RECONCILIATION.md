# Document Delivery Reconciliation

## Purpose

The delivery subsystem must be able to recover from missed workflow events and partial Telegram failures without republishing documents or sending successful deliveries again.

## Invariant

A successful delivery is scoped to `(document_id, recipient_chat_id)`. One recipient's failure does not block another recipient.

## Lifecycle

`Published -> delivery work item -> Telegram message + PDF -> Sent audit`

A failed or missing audit remains eligible for reconciliation. A successful audit is never queued again.

## Trigger model

1. `Global Document Publication` emits a successful `workflow_run` event.
2. Telegram notifier attempts immediate delivery.
3. The notifier's scheduled five-minute run reconciles missed events and transient failures.

## Safety

- Publication is not rolled back because delivery fails.
- No storage-provider URL is exposed to recipients.
- PDF bytes are read from the private primary B2 object.
- Delivery is recipient-scoped and idempotent through the audit record.
- Future recipients can be added through configuration without changing the document lifecycle.

## Current recipient configuration

The production configuration currently uses the existing notification recipient. Additional recipients are intentionally deferred until the core delivery path is stable.
