# School Document Pipeline

Independent cloud workflow for ingesting school documents from Telegram or a monitored Google Drive folder, preserving originals in private Drive storage, recording reviewed metadata in Supabase, and publishing approved public-safe records to a GitHub-hosted portal.

## Status

The resilient staging foundation is deployed. Supabase migrations are applied, the public archive is live, the personal Apps Script project has a verified time-based Drive scan trigger, and the Telegram bot `@UMVLettersBot` has been created. Apps Script web-app version 2 is deployed and Telegram webhook registration returned `ok: true`. Tokens, webhook secrets, and the live endpoint URL remain private.

## Principles

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
- Gemini is an optional server-side first-page suggestion layer; it never changes the original file or publishes automatically.

## Structure

- `apps-script/` serverless ingestion and review application
- `supabase/migrations/` reviewed database changes
- `portal-integration/` read-only public client
- `schemas/` validation contracts
- `tests/` synthetic validation tests
- `docs/` architecture, security, and setup guidance

See [docs/setup-guide.md](docs/setup-guide.md).

## Operational resources

- [Setup guide](docs/setup-guide.md) — staged activation checklist.
- [Operations runbook](docs/operations-runbook.md) — repeatable ingest, review, retry, and archive workflow.
- [Architecture](docs/architecture.md) — components, Drive tree, data movement, lifecycle, and Gemini boundary.
- [Telegram setup](docs/telegram-setup.md) — BotFather, Apps Script properties, webhook, and testing steps.
- [Taxonomy and search](docs/taxonomy-and-search.md) — durable categories and redesign-safe search.
- [Security rules](SECURITY.md) — secret handling and publication boundaries.
