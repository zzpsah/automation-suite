# School Document Pipeline

Independent cloud workflow for ingesting school documents from Telegram or a monitored Google Drive folder, preserving originals in private Drive storage, recording reviewed metadata in Supabase, and publishing approved public-safe records to a GitHub-hosted portal.

## Status

The staging document manager and Supabase review queue are deployed. Telegram uses one-minute Apps Script polling after webhook delivery failed with HTTP 302 redirects. Drive scanning is active; the OCR review worker runs every five minutes. The private portal queries Supabase, subscribes to Realtime, and provides Run AI Review. See [current deployment and handoff](docs/current-deployment.md) for verified results and unfinished work. Secrets remain in Apps Script Properties.

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
