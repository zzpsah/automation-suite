# Pipeline State Resolver v1

## Purpose

`pipeline_state_resolver.py` turns document and intake evidence into a deterministic lifecycle state and safe next action. It has no side effects.

## State contract

`INTAKE_RECEIVED → STORED → PROCESSED → PUBLICATION_PENDING → DELIVERY_PENDING → DELIVERED`

Failure or ambiguous evidence becomes `RECOVERY_REQUIRED` or `UNKNOWN` rather than being silently treated as success.

## Safety

- Processing failures route only to processing recovery/manual review.
- Storage failures route only to storage recovery.
- Completed unpublished documents route to the publication worker; the resolver does not invent publication eligibility.
- Published + approved documents route to delivery reconciliation.
- Confirmed delivery is terminal for the current recipient scope.
- The resolver never deletes, republishes, sends Telegram messages, or changes Supabase state.

## Recovery loop

`observe → resolve → delegate → worker → audit → resolve again`

Repeated runs should converge on the same state until new evidence appears.
