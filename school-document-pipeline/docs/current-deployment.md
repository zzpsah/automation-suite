# Current deployment and handoff

Last consolidated: 10 September 2026. This is a dated deployment record, not a continuous health monitor.

## Components and data movement

```text
Telegram bot -> one-minute Apps Script polling -> Drive 01_Inbox
Direct Drive upload --------------------------> Drive 01_Inbox
                 -> Supabase documents -> Drive 02_Processing
Private portal -> protected review RPC -> processing_jobs
                 -> five-minute Apps Script review worker
                 -> Drive OCR / optional review adapter
                 -> Supabase metadata + suggestions + document_events
                 -> Realtime refresh in private portal
Approved public records -> approved_public_documents -> public archive
```

Four Drive folders live under `All Education Department Letters/Automation System`:
`01_Inbox`, `02_Processing`, `03_Reviewed_Archive`, `04_Manual_Review`.
Folder IDs remain stable when folders move. Registration moves originals to
Processing; automatic movement to final review folders is not implemented.

## Source and deployment locations

- Automation source: branch `feature/resilient-document-taxonomy` in this repository.
- Frontend source/deployment: `zzpsah/umv-tetahali-staging`, branch `main`.
- Private manager: https://zzpsah.github.io/umv-tetahali-staging/private-documents.html
- Public archive: https://zzpsah.github.io/umv-tetahali-staging/school-document-archive.html
- Apps Script uses the concatenated `apps-script/*.gs` source in its editor.
  Time triggers execute saved editor code. Web-app version 3 contains the earlier
  duplicate-reply hotfix; it is not the current polling worker version.

## Configuration

Only publishable Supabase URL/key belong in frontend config. Keep these server
properties private: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`,
`SUPABASE_SERVER_SECRET`, and optional `GEMINI_API_KEY`.

Other Apps Script properties: `SUPABASE_URL`, `AUTHORIZED_TELEGRAM_USER_IDS`,
optional `AUTHORIZED_TELEGRAM_CHAT_IDS`, `DRIVE_INBOX_FOLDER_ID`,
`DRIVE_PROCESSING_FOLDER_ID`, `DRIVE_SCAN_BATCH_SIZE`, `REVIEW_PROVIDER`,
`EXTRACTION_MODE`, optional `GEMINI_MODEL`. `TELEGRAM_POLL_OFFSET` is maintained
by the poller; do not reset it casually. The old `TELEGRAM_WEBAPP_URL` property
is retained for legacy setup, not used by polling.

Current review configuration: `REVIEW_PROVIDER=RULES`, `EXTRACTION_MODE=DRIVE_OCR`.
Gemini key was absent in the last configuration test. Other providers need an
adapter; they are not automatically supported by entering a provider name.

## Security and queue semantics

Authenticated profile admins and trusted JWT reviewer/admin roles may read/update
document records. Ordinary authenticated users do not automatically get access.
`request_document_ai_review` checks identity and role, denies null roles, locks
the document while enqueueing, and reuses an existing queued/processing job.
Anonymous execution is revoked. Realtime is enabled for documents and follows RLS.
The exact SQL is versioned in `supabase/migrations/`; the final authorization
correction is `20260910132000_review_request_authorization.sql`.

AI status: Not Requested -> Requested -> Processing -> Completed or Failed.
Database status remains Needs Manual Review when extraction quality is low.
Completed means the tool finished, not human approval. Public publication and
original-file renaming are not automatic consequences of OCR completion.

## Verified results

- Telegram's repeated replies were traced to HTTP 302 webhook responses.
- Switched to polling with pending updates preserved; verified one polling
  trigger, zero pending updates, and no active webhook.
- Three live repeat deliveries were silently acknowledged; one explicit test
  confirmation was accepted by Telegram. Local regression tests covered five repeats.
- A subsequent Telegram PDF was saved to Drive and registered in Supabase.
- The review worker extracted 5,455 OCR characters from that PDF. Reference/date
  used filename fallback evidence; subject/authority remained unreliable.
  Job status Completed; document status Needs Manual Review; confidence LOW.
- Staging HTML and JavaScript returned HTTP 200 with the manager implementation.
- Transactional database tests verified profile-admin read/request access and
  denied non-admin access with absent role metadata. Test writes were rolled back.
- Pipeline tests and frontend JavaScript syntax checks passed. This checkout
  does not contain the separate site's `check_site.py` or `test_admin.cjs` scripts.

## Remaining work and limitations

- Signed-in browser table, button, and Realtime delivery need end-to-end verification.
- Strict first-page PDF isolation is pending. Both Drive PDF OCR and the current
  Gemini adapter receive the complete file; a first-page prompt is not isolation.
- Gemini has not been activated or live-tested; rules are a limited fallback.
- Automatic classification does not yet synchronize every taxonomy field.
- Private search covers loaded filenames/message IDs with a 500-record limit;
  server pagination and broader office/description search remain to implement.
- Human metadata editing/acceptance, approved filename application, final folder
  movement, and review-completion Telegram notifications remain incomplete.
- Repeated delivery is deduplicated by source message ID, not PDF content hash.
- Worker leasing, stale-job recovery, retries/backoff, and notification recovery
  need strengthening before larger unattended workloads.
- OCR currently runs during intake as well as queued review; separate intake
  from heavy processing before scaling. Reviewed is not proof of human review.

## Operating checks

Run `npm test` from `school-document-pipeline`. Inspect Apps Script Executions
for `pollTelegramUpdates`, `scanDriveInbox`, and `processAiReviewQueue`.
`inspectTelegramDelivery` logs non-secret pending/error fields. For a file,
compare the source message ID, Drive reference, document status, latest job and
events. Do not infer successful processing from an execution's Completed label:
the worker catches errors, so inspect the job's `last_error` too.

No archive reset was performed. Preserve existing files and audit history.
