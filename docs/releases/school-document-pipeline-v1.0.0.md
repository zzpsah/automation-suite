# School Document Pipeline v1.0.0

Release status: FINAL E2E VERIFIED
Date: 2026-09-13

## Verified production path

Telegram → Supabase Intake → Backblaze B2 → B2 verification/SHA-256 → Global Document Processor → GovDOC OCR → metadata normalization → autonomous publication safety gate → Google Drive/public artifact → eLettersBot validated delivery.

## Release gates

- Telegram Input Gateway webhook: verified by live `/health` response.
- Live stage tracking: enabled; one Telegram progress message is edited in place across stages.
- Intake/B2 linkage: verified on real Telegram documents.
- GovDOC OCR: verified on real Telegram document with OCR provenance recorded.
- Processor state consistency: reconciled; completed documents cannot regress to Processing/Failed when verified OCR and backup evidence are present.
- Autonomous publication: enabled; no human approval prerequisite. Safety checks remain mandatory.
- PDF/file delivery: source-format detection, PDF structural validation, conversion protection and checksum verification are enabled.
- eLettersBot regression tests: passing.
- Final real delivery: `ConfirmDetails (3).pdf` successfully delivered by `elettersbot`; 2 pages; 460082 bytes; source and delivery SHA-256 matched exactly.

## Final real-document evidence

Document ID: `2480db26-08b2-4b14-ae06-b77e80c4bea7`

Intake ID: `c70f8f23-73f7-4cce-8cf2-493e3395ad35`

Processing: `Completed`

Publication: `Published`

Telegram source: `UMVInputBot`

OCR provenance: `GovDOC Vision: tesseract Hindi+English`

Delivery bot: `elettersbot`

Delivery format: `pdf`

Conversion: `false` (original valid PDF preserved)

Source SHA-256 = Delivery SHA-256: `ca217ba80885cb9d6d9406390a4ab7fa67e03ea163749948116e69fa538e81a4`

## Non-goals / invariants

- OCR engine behavior is not modified by the release.
- Arbitrary bytes are never relabeled as PDF.
- Publication must not occur without the autonomous safety gate.
- Failed/stale processing states must not be silently treated as success.
- Delivery audit is required; no synthetic success records are allowed.
- Future upgrades must be layered above the established baseline and must preserve these invariants.
