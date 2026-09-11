# GovDOC Vision — Consolidation Status

## 2026-09-12 code-level audit

The canonical `global-automation/govdoc-ocr/` implementation is on `main`. The reusable advanced OCR platform remains on `feature/global-ocr-platform`.

The two histories currently diverge, so the advanced branch must not be blindly merged or copied over `main`. The advanced branch contains substantially more OCR/platform modules, while `main` contains newer repository work.

## Verified implementation gaps to close

1. True page-by-page routing for mixed PDFs (embedded text pages vs scanned pages).
2. Stable structured OCR regions with bounding boxes and provenance.
3. Rich preprocessing/quality diagnostics in the canonical GovDOC response.
4. Deterministic quality-aware backend selection/escalation.
5. Correction corpus and regression contract connected to the canonical service.
6. Benchmark/test matrix covering the public GovDOC service API.

## Reuse policy

Where equivalent capability already exists in `global-automation/ocr/`, port/adapt the tested module rather than rewriting it. Preserve the existing `process_document`, `process_image`, `process_pdf`, and `process_pdf_bytes` compatibility surface.

The School Document Pipeline remains a consumer. Storage, Supabase lifecycle, publication, Telegram and business rules remain outside GovDOC Vision.

## Verification status

A local clone/test run was not available during this audit because the execution environment could not resolve GitHub. Therefore no local pytest/compile pass is claimed here. CI must be checked for the resulting commits before calling the consolidation verified.

## Next implementation sequence

- mixed-PDF page router
- structured regions/provenance
- preprocessing diagnostics
- backend policy
- correction/regression integration
- benchmark and service tests
- documentation update
