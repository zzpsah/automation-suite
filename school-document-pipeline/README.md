# School Document Pipeline

Independent cloud workflow for ingesting school documents from Telegram or a monitored Google Drive folder, preserving originals in private Drive storage, recording reviewed metadata in Supabase, and publishing approved public-safe records to a GitHub-hosted portal.

## Status

Phase 1 scaffold only. No Telegram webhook, Drive trigger, Supabase migration, or production deployment has been activated.

## Principles

- Telegram and Drive are equal ingestion sources.
- AI is optional; MANUAL_ONLY and DRIVE_OCR remain supported.
- Original documents stay private unless explicitly approved.
- Every extracted value is reviewable and missing values remain null.
- Public clients receive only approved, public-safe fields.
- BrowserAct is a separate project and may later provide optional imports.

## Structure

- `apps-script/` serverless ingestion and review application
- `supabase/migrations/` reviewed database changes
- `portal-integration/` read-only public client
- `schemas/` validation contracts
- `tests/` synthetic validation tests
- `docs/` architecture, security, and setup guidance

See [docs/setup-guide.md](docs/setup-guide.md).
