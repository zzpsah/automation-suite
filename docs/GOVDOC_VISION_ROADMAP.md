# GovDOC Vision — Capability & Upgrade Record

## P35-P40 foundation

The canonical `global-automation/govdoc-ocr/` component records the P35-P40 foundation:

- P35: normalized OCR region schema with conservative empty fallback
- P36: deterministic, privacy-safe image diagnostics
- P37: explainable backend selection/escalation policy
- P38: JSONL correction/regression corpus contract
- P39: dependency-free CER/WER/exact-match benchmark metrics
- P40: integration boundary and focused offline contract tests

## P41 — runtime backend policy
Service version `4.1` applies deterministic backend selection during real OCR. Tesseract remains default; optional PaddleOCR can be selected only when installed and policy conditions are met. Selection provenance is recorded.

## P42 — layout and table evidence
Added deterministic OCR-region reading order, visual-row grouping and table-candidate evidence helpers. These helpers never assert that a table exists and never fabricate coordinates.

## P43 — handwriting safety boundary
Added a handwriting capability contract. Current engine explicitly reports that handwriting recognition is **not supported** rather than pretending noisy handwriting OCR is correct.

## P44 — uncertainty review flags
Low-confidence OCR regions can generate structured `requires_review` flags. This creates a safe bridge to future human review without changing source text automatically.

## P45 — no auto-correction of uncertain handwriting
Review flags remain separate from OCR output and intelligence. P45 locks the rule: uncertain handwriting is surfaced for review, never silently corrected or treated as verified fact.

## P46 — backend OCR geometry
Tesseract word boxes are exposed through the optional `pytesseract` integration; PaddleOCR geometry is normalized into the same `OCRRegion` contract. Geometry is propagated into page output and remains empty when unavailable.

## P47 — reading-order reconstruction
Added deterministic line grouping and left-to-right ordering over real OCR regions. The service now exposes `pages[*].lines` when geometry is available. This is reconstruction of existing OCR evidence, not text correction.

## P48 — layout evidence continuity
Table candidates continue to be represented only as evidence rows. No table schema, cell value, or column meaning is invented from geometry alone.

## P49 — empty/partial geometry safety
The reading-order layer has an explicit empty-input contract and preserves sparse/partial OCR geometry without fabricating missing regions or text.

## P50 — runtime contract verification
End-to-end regression coverage now verifies that real Tesseract OCR produces regions and reconstructed lines, while backend provenance and existing no-invention rules remain intact.

## Architecture

`global-automation/govdoc-ocr/` owns OCR, preprocessing, normalization, language packs, government intelligence, diagnostics, regions, backend policy, layout evidence, reading order and regression/benchmark interfaces. The School Document Pipeline owns storage, Supabase lifecycle, publication and Telegram operations.

## Safety

Missing evidence stays missing. OCR confidence and diagnostics are signals, not publication approval, authenticity proof or legal validity. No geometry is invented. No handwriting is claimed as recognized. Reviewed source documents must be added deliberately with provenance and appropriate privacy handling.

## Next phase

- production multi-backend benchmark corpus
- advanced table/field association using verified geometry
- stamp/signature detection as evidence-only signals
- actual handwriting model evaluation on a reviewed private corpus
- semantic/vector retrieval
- larger reviewed Bihar corpus
- OCR-VL/local multimodal integration
