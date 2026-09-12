# eLetters Output Regression — Evidence Ledger

Date: 2026-09-12

## Components
- Intake/source: `UMVInputBot` / `telegram_intake`
- Storage: Backblaze B2
- OCR: GovDOC Vision
- State/publication: `documents` + `Global Document Publication`
- Output/job bot: `@eLettersBot`
- Output workflow: `Global Document Telegram Notifier`
- Output implementation: `telegram_publication_notifier_v3.py`

## Proven working delivery
Document: `d5d55972-42ff-4757-bbfa-ffdbfd2ca437`

Observed live:
- Published: yes
- Approved: yes
- Intake linkage: `00cd2084-b8fd-4485-b63d-07b4ba14db3a`
- Telegram chat: `6914456996`
- B2 object available: yes
- Successful audit: `telegram_publication_notification`
- PDF bytes delivered: `159849`
- Bot: `elettersbot`
- Delivery mode: `private_b2_to_telegram_multipart`

## Regression clues
- The affected document later returned to `processing_status = Processing` despite publication metadata.
- Event history contains repeated source-file-change/reprocess and auto-publish cycles.
- Legacy OCR writer failures occurred during the migration window.
- Gemini 429 failures are explicitly non-fatal and therefore are not, by themselves, a valid explanation for missing PDF delivery.

## Current conclusion
The established eLetters output path exists and has successfully delivered an actual PDF. The active defect is most likely a state/reprocessing/publication handoff regression or a notifier execution failure after the latest changes. Further work must prove which transition/failure occurs before changing code.

## Required proof before closure
- Identify exact triggering commit/state transition.
- Verify notifier workflow run after the fix.
- Verify eLettersBot identity.
- Verify B2 bytes/checksum.
- Verify Telegram `sendMessage` and `sendDocument` success.
- Verify one and only one delivery audit record for the test document/chat.
