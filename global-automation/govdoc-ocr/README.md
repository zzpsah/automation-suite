# GovDOC OCR Engine / GovDOC Vision

Reusable OCR, image-processing and government-document intelligence engine for Indian government documents.

## P35-P50 completed foundation

- **P35 — structured OCR regions:** every OCR page exposes a backward-compatible `regions` array using normalized `{id,bbox,text,confidence,block_type,source}` records. Empty geometry is used when a backend cannot provide reliable regions; geometry is never fabricated.
- **P36 — diagnostics:** OCR pages expose privacy-safe image diagnostics where applicable (dimensions, format, file size, quality/blur proxies, notes). Originals remain untouched.
- **P37 — backend policy:** deterministic, explainable backend selection supports optional escalation to PaddleOCR for low-quality input when it is installed; Tesseract remains the default.
- **P38 — correction/regression contract:** JSONL regression cases preserve source reference, expected text and review notes; corrections should become explicit regression cases.
- **P39 — benchmark metrics:** dependency-free Unicode-safe CER/WER-style edit metrics and exact-match benchmark output are available for offline regression.
- **P40 — integration contract:** service output, diagnostics, regions, backend policy and regression/benchmark boundaries are documented and covered by focused tests. No storage/publication responsibility moved into GovDOC.
- **P41 — OCR geometry propagation:** Tesseract can expose word-level bounding boxes through `pytesseract` when available; PaddleOCR geometry is normalized into the same contract. Backend geometry is propagated into `pages[*].regions` without inventing coordinates.
- **P42 — deterministic layout intelligence:** geometry-aware line grouping, likely-column detection, column-aware reading order and compact layout summaries are available from OCR regions.
- **P43 — table intelligence:** repeated x-alignment across multiple visual rows produces table-candidate evidence and candidate column anchors. The engine does not claim a table exists merely from OCR text.
- **P44 — document structure:** strong lexical signals can classify region candidates as heading-signal/body/unknown. Structure output is explicitly evidence-only.
- **P45 — metadata/date validation:** date candidates are preserved with source text offsets and calendar-validity status. Invalid dates are flagged rather than silently corrected.
- **P46 — provenance contract:** storage-neutral `EvidenceRef` pointers can identify source, page, region and field without moving storage responsibility into GovDOC.
- **P47 — confidence aggregation:** region confidence statistics provide transparent mean/minimum and low-confidence signals; confidence is explicitly not publication approval.
- **P48 — multipage consistency:** page counts, extraction methods, OCR pages, embedded pages, backend set and mixed-processing signals are summarized without changing page content.
- **P49 — search index contract:** a compact storage-neutral search record exposes source text plus key government-document metadata for downstream indexing. Persistence remains the caller's responsibility.
- **P50 — release gate:** dependency-free contract validation checks required result keys and sequential page numbering before a consumer treats a result as structurally valid.

## Current capabilities

- PDF embedded-text extraction
- **page-level mixed PDF routing**
- scanned-PDF OCR
- Hindi + English Tesseract baseline
- optional PaddleOCR backend
- direct JPG/JPEG/PNG/TIFF/WebP image input
- conservative image preprocessing
- page-level OCR results, regions and diagnostics
- raw + normalized text
- versioned result envelope (`schema_version` 1.1)
- evidence-based government-document intelligence
- subject, authority, document type, actions and deadlines
- Bihar district/office vocabulary foundation
- correction/normalization architecture
- deterministic backend policy
- geometry-aware layout/reading-order analysis
- conservative table/structure/date evidence modules
- provenance and confidence contracts
- multipage processing signals
- storage-neutral search-index contract
- dependency-free release-gate checks
- stable `ocr_service.py` consumer interface

## Import compatibility

The canonical implementation remains under `global-automation/govdoc-ocr/`. A lightweight `global-automation/govdoc_ocr/` package alias exposes the stable Python import name `govdoc_ocr` without duplicating implementation files. CI sets `PYTHONPATH` for both the automation root and canonical OCR source tree. A pytest compatibility bootstrap preserves legacy top-level imports used by older tests, while the package import path is the preferred production/test interface. The offline GovDOC smoke test uses the stable package imports directly. The deterministic verification loop also compiles the alias package explicitly.

## P42-P50 module contract

The P42-P50 helpers are additive and storage-neutral:

- `layout.py` — lines, columns and reading order.
- `table_intelligence.py` — repeated-column/table evidence.
- `document_structure.py` — heading/body evidence.
- `metadata_validation.py` — date candidate and calendar validation.
- `provenance.py` — explicit source/page/region/field evidence pointers.
- `confidence.py` — transparent OCR confidence aggregation.
- `multipage.py` — cross-page processing signals.
- `search_index.py` — downstream search-record contract; no persistence.
- `release_gate.py` — minimal structural release checks.

These helpers do not own Supabase, Backblaze B2, Telegram, publication, retries or business rules. They are designed to be consumed safely by the existing School Document Pipeline.

## School Document Pipeline integration

`global-automation/scripts/document/document_processor.py` contains a **safe opt-in GovDOC Vision integration boundary**. Set `GOVDOC_VISION_ENABLED=1` to make the shared GovDOC adapter the primary extractor. If the adapter cannot initialize, the processor logs the condition and retains the existing legacy extractor. This keeps storage, B2, Supabase lifecycle, duplicate detection, retry state and publication ownership in the existing pipeline while the reusable OCR engine is validated in the target runtime.

The adapter now propagates the intake's original filename into the GovDOC processing call. This preserves correct document-type routing and keeps the process-local cache isolated by both content checksum and filename. Existing one/two-argument legacy extractor compatibility remains intact through adapter defaults and fallback calls.

The integration is deliberately opt-in until the release gates below have a verified CI/target-runtime result. This is a release-safety decision, not a claim that production OCR has already been validated.

## OCR geometry contract

`pages[*].regions` is a list of pixel-space bounding boxes `[x1, y1, x2, y2]`. Region text and confidence are backend-derived. Tesseract geometry is optional because `pytesseract` is not a hard dependency. If geometry cannot be obtained reliably, the list remains empty. Coordinates are never guessed from text length or page dimensions.

## PDF routing contract

A PDF is evaluated page-by-page. A page with at least `min_embedded_chars` non-whitespace characters uses embedded text; sparse/empty pages are rendered and sent through the selected OCR backend. `pages` preserves order and records `extraction_method` as `embedded-text` or `ocr:<backend>`.

## OCR backend policy

Tesseract Hindi + English remains the free/default baseline. PaddleOCR is optional. Backend policy is deterministic and explainable; optional escalation does not make PaddleOCR a hard dependency.

## Government intelligence

The intelligence layer is evidence-first. Missing evidence stays missing; OCR confidence is never publication approval. Calling applications own storage, Supabase lifecycle, publication, Telegram and business rules.

## Improvement loop

`real document → OCR → identify error → correction with provenance → regression test → benchmark → deploy`

Preserve raw OCR and correction provenance. Do not silently rewrite source text.

## Release-readiness gates

The product is considered **production-ready only when all required gates are verified**, not merely when the source code exists:

1. **Build gate:** canonical source, stable alias and document-pipeline code compile.
2. **Unit gate:** GovDOC OCR tests and adapter contract tests pass.
3. **Smoke gate:** GovDOC intelligence smoke test and offline pipeline smoke pass.
4. **Fixture gate:** embedded-text, scanned Hindi/English and mixed-page PDF fixtures produce structurally valid results with page order preserved.
5. **Contract gate:** `release_gate.validate_result()` passes for representative outputs.
6. **Integration gate:** School Document Pipeline uses GovDOC under explicit `GOVDOC_VISION_ENABLED=1` without moving storage/publication ownership.
7. **Resilience gate:** missing B2, OCR failure, duplicate input, concurrent claim and retry paths fail safely and remain idempotent.
8. **Evidence gate:** no fabricated text, geometry or metadata; uncertain fields remain uncertain.
9. **Operational gate:** CI result is independently verified on the final commit; no “green” status is inferred from local code inspection.
10. **Rollback gate:** disabling `GOVDOC_VISION_ENABLED` restores the legacy extraction path without changing durable storage schema or publication behavior.

### Current release status

**NOT YET DECLARED PRODUCTION-READY.** Code-level integration and deterministic offline verification infrastructure are present, but a completed CI/target-runtime verification result and representative document-fixture validation still need to be observed before the final readiness claim.

## Non-goals

- No invented OCR text or geometry.
- No automatic publication approval from confidence.
- No silent correction of source text.
- No storage/database ownership inside this OCR package.
- No hard dependency on PaddleOCR.
- No destructive rewrite of the existing School Document Pipeline.

## Future / experimental

- advanced stamp/signature detection
- handwriting recognition
- semantic/vector retrieval with real embeddings
- larger reviewed Bihar corpus
- OCR-VL/local multimodal models
