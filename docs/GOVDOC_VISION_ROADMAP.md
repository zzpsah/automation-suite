# GovDOC Vision — Capability & Upgrade Record

## P35-P40 canonical completion

The canonical `global-automation/govdoc-ocr/` component now records the P35-P40 foundation:

- P35: normalized OCR region schema with conservative empty fallback
- P36: deterministic, privacy-safe image diagnostics
- P37: explainable backend selection/escalation policy
- P38: JSONL correction/regression corpus contract
- P39: dependency-free CER/WER/exact-match benchmark metrics
- P40: integration boundary and focused offline contract tests

The service API remains backward-oriented: new page fields (`regions`, `diagnostics`) are additive, while raw text, normalized text, metadata and page order remain available. Service envelope is now `schema_version` 1.1 and service version 4.0.

## Canonical architecture

`global-automation/govdoc-ocr/` owns OCR, preprocessing, normalization, language packs, government intelligence, diagnostics, regions, backend policy and benchmark/regression interfaces. The School Document Pipeline remains outside this package and owns storage, Supabase lifecycle, publication and Telegram operations.

## Evidence and safety boundary

Government intelligence is evidence-first. Missing evidence stays missing. OCR confidence and visual diagnostics are signals, not publication approval, authenticity proof, or legal validity. Region geometry is emitted only when a backend can supply it reliably; the baseline service uses an explicit empty list rather than invented coordinates.

## Backend policy

Tesseract remains the free/default baseline. PaddleOCR is optional and may be selected/escalated only when installed and permitted by the deterministic policy. Future OCR-VL/local vision backends must satisfy the same boundary and be benchmarked before default adoption.

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
