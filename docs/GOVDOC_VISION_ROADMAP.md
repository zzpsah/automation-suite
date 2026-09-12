# GovDOC Vision — Capability & Upgrade Record

## P35-P40 foundation

The canonical `global-automation/govdoc-ocr/` component records the P35-P40 foundation:

- P35: normalized OCR region schema with conservative empty fallback
- P36: deterministic, privacy-safe image diagnostics
- P37: explainable backend selection/escalation policy
- P38: JSONL correction/regression corpus contract
- P39: dependency-free CER/WER/exact-match benchmark metrics
- P40: integration boundary and focused offline contract tests

## P41 runtime backend policy

Service version `4.1` now applies the deterministic P37 backend policy during real image/PDF OCR. Tesseract remains the default. If the optional PaddleOCR package is actually installed and the image diagnostic quality proxy is below the configured threshold, the service may select PaddleOCR. The selected backend, requested backend, reason and escalation flag are recorded in the result for traceability.

This is not an OCR-confidence claim. Image quality diagnostics are conservative signals only. If PaddleOCR is unavailable, the default Tesseract path remains unchanged.

`process_pdf_bytes()` also accepts an explicit backend so callers using the byte-oriented API do not lose backend control.

## Canonical architecture

`global-automation/govdoc-ocr/` owns OCR, preprocessing, normalization, language packs, government intelligence, diagnostics, regions, backend policy and benchmark/regression interfaces. The School Document Pipeline remains outside this package and owns storage, Supabase lifecycle, publication and Telegram operations.

## Evidence and safety boundary

Government intelligence is evidence-first. Missing evidence stays missing. OCR confidence and visual diagnostics are signals, not publication approval, authenticity proof, or legal validity. Region geometry is emitted only when a backend can supply it reliably; the baseline service uses an explicit empty list rather than invented coordinates.

## Regression loop

`real document → OCR → identify error → correction with provenance → JSONL regression case → CER/WER benchmark → review → deploy`

No production corpus is fabricated by the engine. Reviewed source documents should be added deliberately, with provenance and appropriate privacy handling.

## Remaining experimental roadmap

- production-quality multi-backend scoring against a reviewed corpus
- real word/line geometry from Tesseract/Paddle adapters
- advanced layout/table/stamp/signature detection
- handwriting recognition
- semantic/vector retrieval using real embeddings
- larger reviewed Bihar corpus and field-level dashboards
- OCR-VL/local multimodal integration
