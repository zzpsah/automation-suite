# GovDOC OCR Engine / GovDOC Vision

Reusable OCR, image-processing and government-document intelligence engine for Indian government documents.

## P35-P40 completed foundation

- **P35 — structured OCR regions:** every OCR page now exposes a backward-compatible `regions` array using normalized `{id,bbox,text,confidence,block_type,source}` records. Empty geometry is used when a backend cannot provide reliable regions; geometry is never fabricated.
- **P36 — diagnostics:** OCR pages expose privacy-safe image diagnostics where applicable (dimensions, format, file size, quality/blur proxies, notes). Originals remain untouched.
- **P37 — backend policy:** deterministic, explainable backend selection supports optional escalation to PaddleOCR for low-quality input when it is installed; Tesseract remains the default.
- **P38 — correction/regression contract:** JSONL regression cases preserve source reference, expected text and review notes; corrections should become explicit regression cases.
- **P39 — benchmark metrics:** dependency-free Unicode-safe CER/WER-style edit metrics and exact-match benchmark output are available for offline regression.
- **P40 — integration contract:** service output, diagnostics, regions, backend policy and regression/benchmark boundaries are documented and covered by focused tests. No storage/publication responsibility moved into GovDOC.

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
- storage-neutral keyword search boundary
- stable `ocr_service.py` consumer interface

## PDF routing contract

A PDF is evaluated page-by-page. A page with at least `min_embedded_chars` non-whitespace characters uses embedded text; sparse/empty pages are rendered and sent through the selected OCR backend. `pages` preserves order and records `extraction_method` as `embedded-text` or `ocr:<backend>`.

## OCR backend policy

Tesseract Hindi + English remains the free/default baseline. PaddleOCR is optional. Backend policy is deterministic and explainable; optional escalation does not make PaddleOCR a hard dependency.

## Government intelligence

The intelligence layer is evidence-first. Missing evidence stays missing; OCR confidence is never publication approval. Calling applications own storage, Supabase lifecycle, publication, Telegram and business rules.

## Improvement loop

`real document → OCR → identify error → correction with provenance → regression test → benchmark → deploy`

Preserve raw OCR and correction provenance. Do not silently rewrite source text.

## Future / experimental

- richer backend scoring with a reviewed corpus
- advanced table/layout/stamp/signature detection
- handwriting recognition
- semantic/vector retrieval with real embeddings
- larger reviewed Bihar corpus
- OCR-VL/local multimodal models
