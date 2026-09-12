# eLetters Output Regression — 2026-09-12

## Purpose
Document the verified state of the existing eLettersBot output path and the regression observed during GovDOC migration/reprocessing. This is a diagnostic record, not a new architecture.

## Existing intended path
`Telegram intake → B2 storage → GovDOC Vision OCR → document metadata/state → publication → eLettersBot → Telegram message + actual PDF`

`eLettersBot` is the output/job bot. It is not the intake/source bot.

## Verified implementation
Workflow: `.github/workflows/global-document-telegram-notifier.yml`
- `Global Document Telegram Notifier` runs after successful publication, manually, and every 5 minutes.
- Its job is explicitly `Published document → eLettersBot private PDF delivery`.
- It invokes `global-automation/scripts/document/telegram_publication_notifier_v3.py`.
- Output bot username is `eLettersBot`.
- Delivery downloads the private B2 object and uploads PDF bytes to Telegram with `sendDocument`; storage URLs are not exposed.

Notifier selection:
- `publication_status = Published` and `approved_for_publication = true`.
- Intake is resolved from `documents.source_message_id`.
- B2 object key is read from `telegram_intake.metadata.storage.b2_key`.
- B2 object is downloaded and checksum-verified when available.
- Recipients come from configured chat IDs plus intake `telegram_chat_id`.
- `document_operations_audit` prevents duplicate sends.
- It sends a Telegram message and then the actual PDF.
- Successful delivery is recorded as `telegram_publication_notification`.

## Live evidence
Supabase project: `sxfnrwugsyfypqgfglzc`.

Document `d5d55972-42ff-4757-bbfa-ffdbfd2ca437` was verified live as published and approved. Its `source_message_id` resolves to intake `00cd2084-b8fd-4485-b63d-07b4ba14db3a`, Telegram chat `6914456996`, with an available B2 object and verified storage metadata.

A successful `telegram_publication_notification` audit record exists for this exact document/chat, showing bot `elettersbot`, 159,849 bytes, SHA-256 `0b7f6841aad96c425c883fcc3762210f393e82299f13c190f9f32a2cc3cafc2c`, delivery mode `private_b2_to_telegram_multipart`, and timestamp `2026-09-12T03:31:42.840203+00:00`.

Therefore the existing eLetters delivery mechanism has demonstrably worked against the live system; this is not a missing-feature problem.

## Regression/state anomaly
The same document later appears with `processing_status = Processing` while retaining publication metadata. Other documents show `Processing Failed` with the retired legacy OCR writer guard during migration/reprocessing. The event history for the affected document also shows repeated `SOURCE_FILE_CHANGED_AND_REPROCESSED` and `AUTO_PUBLISHED` events, alongside non-fatal Gemini quota errors.

Investigation is therefore focused on state transitions/reprocessing and the publication→notifier handoff, not on redesigning OCR or eLetters.

## Known historical failure modes
1. Telegram HTTP 400 during a prior notification attempt.
2. Notification skipped when valid `telegram_intake` linkage could not be resolved.
3. Legacy OCR writer rejection during migration before the successful migration rerun.

## Remediation guardrails
- No fake documents or fake delivery events.
- No GovDOC OCR feature changes for eLetters testing.
- Preserve the established eLettersBot delivery contract.
- Make only minimal, evidence-backed fixes.
- Do not declare fixed until actual PDF delivery is verified.

## Next investigation
1. Trace `Global Document Publication` state transitions and recent commits.
2. Identify what moves an already-published document back to `Processing`/`Unpublished`.
3. Check publication/reprocessing races.
4. Check notifier workflow runs/logs for exact failures and Telegram responses.
5. Harden idempotency/state handling only if evidence requires it.
