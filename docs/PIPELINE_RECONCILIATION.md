# End-to-End Document Pipeline Reconciliation

## Scope

Reconciliation observes the lifecycle from intake/storage through processing, publication, and Telegram delivery. It does not replace workers and does not perform destructive actions.

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

## Operational model

`observe → classify → delegate → worker acts → audit → observe again`

The system therefore becomes self-healing through bounded, stage-specific workers while preserving Supabase as the control-plane source of truth.
