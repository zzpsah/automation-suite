# Verify School Document Pipeline

Run the repository's deterministic verification loop for the School Document Pipeline.

## Required checks

1. Compile `global-automation/scripts/document`.
2. Compile `global-automation/govdoc-ocr`.
3. Run GovDOC OCR tests.
4. Run the GovDOC OCR smoke test.
5. Run the offline School Document Pipeline smoke test.
6. If a production workflow fails, classify the failure before changing OCR code. In particular, distinguish storage/B2 failures from OCR failures.

## Important

A successful offline loop does not prove B2/Supabase production connectivity. Production verification must be reported separately with the exact failed or verified boundary.
