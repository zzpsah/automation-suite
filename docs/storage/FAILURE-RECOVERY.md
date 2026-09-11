# UMV Storage Failure and Recovery

## Design goal

A temporary provider failure must not require the operator to manually copy files or repeatedly submit them through Telegram.

## R2 fails, B2 succeeds

```text
R2 upload/retrieval failure
        |
        v
Retry with backoff
        |
        v
B2 verified?
   |          |
  YES         NO
   |          |
serve/recover  keep retry state
from B2       and alert only if exhausted
        |
        v
repair R2 automatically
```

## B2 fails, R2 succeeds

The R2 primary copy remains authoritative for the file bytes. The backup job retries B2 independently until the configured policy succeeds.

## Both fail

Keep the Supabase intake record and all available metadata. Mark the storage job failed and retain enough information for reconciliation. Do not silently delete the intake record.

## Corrupt/mismatched copy

Compare the stored SHA-256 and size against the canonical metadata. A mismatch means the copy is invalid. Re-upload from the known-good provider copy or, if necessary, from a retained source while it is still available.

## Reconciliation

A scheduled job should periodically find records where:

- R2 is missing but B2 exists;
- B2 is missing but R2 exists;
- object size/hash does not match metadata;
- storage status is stuck in an in-progress state.

It should repair these automatically and update Supabase status/audit fields.

## Human escalation

Only escalate after automatic retries/reconciliation fail, or when provider credentials/account access have been revoked or require manual verification.
