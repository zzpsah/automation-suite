# School Document Pipeline

Independent cloud workflow for ingesting school documents from Telegram or a monitored Google Drive folder, preserving originals in private Drive storage, recording reviewed metadata in Supabase, and publishing approved public-safe records to a GitHub-hosted portal.

## Status

The staging document manager and Supabase review queue are deployed. Telegram uses one-minute Apps Script polling after webhook delivery failed with HTTP 302 redirects. Drive scanning is active; the OCR review worker runs every five minutes. The private portal queries Supabase, subscribes to Realtime, and provides Run AI Review. See [current deployment and handoff](docs/current-deployment.md) for verified results and unfinished work. Secrets remain in Apps Script Properties.

## Operator quick reference

Documentation checked against repository source on **10 September 2026**. Live results below are the dated checkpoint in [current deployment](docs/current-deployment.md), not a new health check. This README update does not deploy Apps Script, change database policies, or merge the feature branch.

| Component | Location / purpose |
| --- | --- |
| Telegram | [@UMVLettersBot](https://t.me/UMVLettersBot), display name `Edu. Dept. Letters Mgmt.`; document intake |
| Bot administration | [@BotFather](https://t.me/BotFather); create/revoke tokens privately |
| Apps Script editor | [Open pipeline source](https://script.google.com/home/projects/1mnfO0RkzYwdmyIqKTTeFFe6yOiFDdZzEjawuoCB1SWz6R5flYacuqQdi/edit) |
| Apps Script configuration | [Project Settings → Script Properties](https://script.google.com/home/projects/1mnfO0RkzYwdmyIqKTTeFFe6yOiFDdZzEjawuoCB1SWz6R5flYacuqQdi/settings) |
| Apps Script project ID | `1mnfO0RkzYwdmyIqKTTeFFe6yOiFDdZzEjawuoCB1SWz6R5flYacuqQdi` (an identifier, not a token) |
| Backend source | [apps-script/](apps-script/), this repository, branch `feature/resilient-document-taxonomy` |
| Database | Supabase project `sxfnrwugsyfypqgfglzc`; versioned [migrations](supabase/migrations/) |
| Private portal | [Document manager](https://zzpsah.github.io/umv-tetahali-staging/private-documents.html); authorized login required |
| Public portal | [Approved document archive](https://zzpsah.github.io/umv-tetahali-staging/school-document-archive.html) |
| Frontend repository | [zzpsah/umv-tetahali-staging](https://github.com/zzpsah/umv-tetahali-staging), `main`; `private-documents.html`, `assets/private-document-manager.js`, `assets/document-archive-config.js` |

The editor/settings links require existing Google project permissions; they do not grant access. Private Drive folder IDs, sender allowlist values, tokens and server keys are intentionally not copied into this public README. Find the configured folder IDs in Script Properties and open them with the authorized Google account.

## Complete workflow and file locations

```text
My Drive/
└── All Education Department Letters/
    └── Automation System/
        ├── 01_Inbox/             Telegram downloads and direct uploads
        ├── 02_Processing/        Registered originals awaiting review
        ├── 03_Reviewed_Archive/  Reserved final destination
        └── 04_Manual_Review/     Reserved manual-review destination

Telegram upload ── pollTelegramUpdates (~1 minute) ─┐
Direct Inbox upload ── scanDriveInbox (~10 minutes) ┤
                                                  v
                     source-identity check → Supabase document + audit event
                                      → intake extraction/suggestions
                                      → move original to 02_Processing
                                      → Telegram registration reply (Telegram intake)

Authorized portal → Run AI Review → request_document_ai_review(document UUID)
                  → processing_jobs → processAiReviewQueue (~5 minutes)
                  → OCR / review adapter → metadata, suggestions, events
                  → Supabase Realtime → private portal refresh

Explicit public approval → approved_public_documents → public archive
```

1. The Telegram handler permits a configured sender **or** configured chat. Empty allowlists reject all uploads. It downloads supported media into Inbox while preserving the original filename.
2. Intake records source identity, original/display filename, MIME type, size and private Drive reference. Telegram identity is `chat ID:message ID`; direct Drive intake uses the file identity. Repeated delivery of an existing Telegram message is silent. This is not content-hash deduplication across different uploads/sources.
3. Intake currently performs extraction before returning, stores metadata and audit events, and then moves the registered original into Processing. Heavy OCR is therefore not fully separated from intake yet. Failures need inspection; an existing row is not proof every later step succeeded.
4. The private manager reads permitted Supabase rows, shows file/status/link information, filters records and subscribes to Realtime. Run AI Review queues work through the protected RPC. Existing active jobs are reused rather than duplicated.
5. The worker updates the review job and document metadata. AI `Completed` means a tool finished, **not human approval**. Low-quality results remain `Needs Manual Review`; inspect evidence and error fields rather than trusting a generic execution-completed label.
6. Final-folder moves, human accept/edit controls, physical filename changes and worker-completion Telegram messages are **not complete**. The two final folders do not yet represent an automatic state transition. Never move/delete originals just to make the folder tree match a status.
7. Originals remain private. Public output must come from explicitly approved, public-safe records, not a direct dump of private documents. No archive reset has been performed.

The Google account running the triggers needs access to the configured folders. When the Drive owner and script account differ, grant the intended account appropriate folder access privately; do not enable public link sharing. Folder moves preserve IDs, so use IDs rather than assuming a pathname is an API address.

## Script Properties: what goes where

Open the settings link above, choose **Script Properties**, and save values there—not in `.gs` files, browser JavaScript, GitHub, screenshots or chat.

| Property | Purpose / configuration |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Secret token from BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Separate long random secret; still required by the shared handler invoked internally by polling |
| `AUTHORIZED_TELEGRAM_USER_IDS` | Comma-separated numeric sender IDs, not usernames |
| `AUTHORIZED_TELEGRAM_CHAT_IDS` | Optional comma-separated permitted chat IDs; membership permits intake independently of sender allowlist |
| `SUPABASE_URL` | Actual database API project URL |
| `SUPABASE_SERVER_SECRET` | Server-only database credential; never the frontend key |
| `DRIVE_INBOX_FOLDER_ID` | ID of `01_Inbox` |
| `DRIVE_PROCESSING_FOLDER_ID` | ID of `02_Processing` |
| `DRIVE_SCAN_BATCH_SIZE` | Start at `10`; code clamps to 1–50 |
| `EXTRACTION_MODE` | Reported current value `DRIVE_OCR`; use `MANUAL_ONLY` where full-document OCR is unsuitable |
| `REVIEW_PROVIDER` | Reported current value `RULES`; implemented alternatives `NONE` and `GEMINI` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional Gemini credentials/model; Gemini was not active or live-tested at the checkpoint |
| `GEMINI_ENABLED` | Legacy provider fallback when explicit `REVIEW_PROVIDER` is absent; prefer explicit provider configuration |
| `TELEGRAM_POLL_OFFSET` | Automatically maintained cursor; do not casually clear/reset |
| `TELEGRAM_WEBAPP_URL` | Legacy webhook configuration; not required for active polling |

The frontend receives only publishable Supabase configuration and uses authorized login plus database RLS. Ordinary authenticated users do not automatically receive private-document access. Do not use user-editable profile metadata as an authorization grant.

## Apps Script source and trigger setup

The recorded deployment combines `apps-script/*.gs` into the editor source. For maintenance, keep each module once (separate `.gs` files are also valid); do not retain duplicate functions when replacing a combined file. Keep the repository manifest [appsscript.json](apps-script/appsscript.json) aligned and enable the Drive advanced service. Save source before testing.

| Entry point | Use |
| --- | --- |
| `installTelegramPolling` | Install one-minute polling if absent and disable webhook delivery while preserving pending updates |
| `pollTelegramUpdates` | Read up to 10 updates, invoke shared handler, advance offset after handled updates |
| `installDriveScanTrigger` | Replace this handler's existing scanner triggers with one ten-minute trigger |
| `scanDriveInbox` | Scan configured Inbox batch and register files |
| `installAiReviewTrigger` | Install five-minute review worker if absent |
| `configureFreeReviewMode` | Set `RULES` + `DRIVE_OCR` and install review worker; changes configuration, so do not rerun blindly |
| `processAiReviewQueue` | Process queued review jobs; inspect job errors as well as executions |
| `inspectTelegramDelivery` | Inspect non-secret webhook/pending/error diagnostics |

For an existing installation, first inspect **Triggers** and **Executions** in the editor sidebar. Do not create parallel triggers by replaying every setup step. Time triggers use saved editor source; committing to GitHub does not update Apps Script. The historical web-app version 3 is not evidence that the current polling worker source was redeployed. Polling does not need a new web-app deployment.

### Telegram replies and token rotation

Successful intake sends `Document registered: <document UUID>` and, when available, a review-suggestion report containing suggested metadata/display filename. That reply does not prove human review, public publication or a physical Drive rename. Unsupported messages receive attachment guidance; repeated delivery of the same registered message produces no new reply. A later queue-worker review currently does **not** send a completion report back to Telegram.

If a token is exposed, revoke it with BotFather and paste the replacement only into `TELEGRAM_BOT_TOKEN`. Preserve the polling offset and document history. Use `inspectTelegramDelivery` and a controlled test to verify recovery; if restoring the polling transport, `installTelegramPolling` disables webhook delivery without dropping pending updates. **Do not call `registerTelegramWebhook` for this polling deployment**: the previous webhook's HTTP 302 responses caused repeated deliveries.

## OCR, naming and redesign-safe metadata

Review suggestions can include document title, issuing authority, printed date, reference number, subject, deadline, required action, category, priority, portal description and display filename. Preserve the original and distinguish OCR evidence from filename fallback and tool interpretation. Stable document IDs and separate metadata allow the portal layout and category labels to change without relocating originals or losing history; see [taxonomy and search](docs/taxonomy-and-search.md).

**First-page-only processing is still pending.** Current Drive OCR converts the complete PDF to a temporary Google Doc and trashes the conversion afterward; the original is preserved. The optional Gemini adapter also receives the full file, even with a first-page prompt. Use manual review when that scope is unacceptable. Other AI/OCR tools need an explicit adapter and verification, not just a new provider name. No paid provider is required for the current rules/OCR mode, but service quotas still apply.

## Safe test and troubleshooting checklist

1. With Node.js 20+ installed, run `npm test` from `school-document-pipeline/`. These are synthetic tests, not deployment checks; no Python or `pip install` is required.
2. Check the selected Apps Script project, folder permissions, saved properties and existing three trigger handlers. Keep secrets out of logs.
3. Send one non-sensitive sample file to the bot **or** upload it to Inbox. Record its source identity and check for one new document, original Drive file, audit event and expected registration response.
4. Log into the private portal as an authorized reviewer/admin. Verify filename, size, source message, statuses and working Drive link. If absent, inspect authentication, RLS, query filters and browser errors; do not weaken access policies to reveal it.
5. Request AI review once. Check `processing_jobs`, document AI/database statuses and events. Test Realtime in the signed-in page. Examine `last_error` if the worker appears completed but the document did not change.
6. Review extracted fields against the source; do not approve unreliable values. Verify original filename/file is intact. Public listing requires separate explicit approval.
7. For repeated notifications, inspect webhook state, duplicate triggers and source identity before resetting anything. For Drive failures, verify the trigger owner's permissions. For stalled jobs, inspect errors and obtain a scoped recovery plan rather than deleting history.

At the recorded checkpoint, Telegram-to-Drive-to-Supabase intake and one OCR job were verified; the job required manual review. Signed-in portal rendering/button/Realtime, strict first-page processing, final folder automation, human metadata acceptance, broad server-side search/pagination, content-hash deduplication, durable retry recovery and review-completion Telegram notifications remain unfinished. See [current deployment](docs/current-deployment.md) for evidence and limitations.

## Design principles

- Telegram and Drive are equal ingestion sources.
- AI is optional; MANUAL_ONLY and DRIVE_OCR remain supported.
- Original documents stay private unless explicitly approved.
- Every extracted value is reviewable and missing values remain null.
- Public clients receive only approved, public-safe fields.
- BrowserAct is a separate project and may later provide optional imports.
- All source documents remain private in Drive; publication requires an explicit review decision.
- Category keys are stable, while labels, aliases, office terms, and content terms are versioned.
- Search is based on structured document fields, not on fixed page categories.
- The Drive layout is `All Education Department Letters/Automation System/` with Inbox, Processing, Reviewed Archive, and Manual Review subfolders.
- Telegram confirms registration, while review and publication remain human-controlled.
- Gemini is an optional review adapter; it is not configured or live-tested. Current PDF OCR converts the entire PDF; first-page isolation is pending.

## Structure

- `apps-script/` serverless ingestion and review application
- `supabase/migrations/` reviewed database changes
- `portal-integration/` public client and private-manager integration documentation
- `schemas/` validation contracts
- `tests/` synthetic validation tests
- `docs/` architecture, security, and setup guidance

See [docs/setup-guide.md](docs/setup-guide.md).

## Operational resources

- [Setup guide](docs/setup-guide.md) — staged activation checklist.
- [Operations runbook](docs/operations-runbook.md) — repeatable ingest, review, retry, and archive workflow.
- [Architecture](docs/architecture.md) — components, Drive tree, data movement, lifecycle, and Gemini boundary.
- [Telegram setup](docs/telegram-setup.md) — BotFather, properties, polling, and legacy webhook notes.
- [Current deployment](docs/current-deployment.md) — complete handoff, tests, configuration and remaining limitations.
- [Taxonomy and search](docs/taxonomy-and-search.md) — durable categories and redesign-safe search.
- [Security rules](SECURITY.md) — secret handling and publication boundaries.
