# GovDOC Vision — Capability & Upgrade Record

## What is now in the canonical component

`global-automation/govdoc-ocr/` now contains the promoted foundation from the advanced OCR work:

- pluggable OCR backend contract
- Tesseract Hindi+English backend
- optional PaddleOCR backend adapter
- image preprocessing layer
- direct JPG/JPEG/PNG/TIFF/WebP processing
- PDF embedded-text path
- scanned PDF rendering and page OCR
- page-level structured results
- evidence-based Government Document Intelligence v2
- conservative government-text normalization
- Bihar district and education-office vocabulary foundation
- Bihar education-domain vocabulary and OCR-alias detection
- storage-neutral keyword search interface
- compatibility-oriented service API

The School Document Pipeline remains outside this package and continues to own storage, Supabase lifecycle, publication and Telegram operations.

## Intelligence engine

Government intelligence is evidence-first. It prioritizes header authority, labelled official subject, document-type evidence, actionable instructions and source dates. Missing evidence stays missing; OCR confidence is not publication approval.

The intelligence layer is now exercised independently from storage: CI can test OCR, language resolution, intelligence and search without requiring a live B2/Supabase document. This prevents infrastructure/data-integrity failures from being mistaken for OCR regressions.

## Bihar language pack — v0.3.0

The Bihar pack is a two-layer vocabulary system:

1. `bihar_districts.json` — district, office and school identity vocabulary.
2. `bihar_education.json` — education administration, school types, academic terms, staff/service, infrastructure, welfare, document labels, OCR aliases and conservative Unicode normalization.

The resolver:

- normalizes safe Unicode variants before matching
- detects education-domain terms with source evidence
- detects known OCR aliases without silently rewriting source text
- returns canonical district/office keys only when evidence is present
- marks multiple district/office candidates as ambiguous instead of guessing
- never infers district/block from a person's name
- preserves original source wording for downstream consumers

Every accepted correction should become a regression case.

## CI verification boundary

The canonical offline test suite now performs:

- Python compilation of document and GovDOC code
- backend registration checks
- Government Intelligence evidence tests
- Bihar district/office resolution tests
- OCR-alias detection tests
- ambiguity/no-guessing tests
- keyword-search tests
- real Tesseract image OCR using a generated Hindi/English document sample
- preprocessing metadata checks
- existing pipeline smoke tests

The test fixture is intentionally self-contained and does not depend on B2, Supabase, Telegram or private production records.

## OCR/Vision backend policy

Tesseract remains the free baseline. PaddleOCR is optional and selectable; the service must continue to work when PaddleOCR is not installed. Future OCR-VL/local vision models can implement the same backend boundary and should be benchmarked before becoming defaults.

## Search

A storage-neutral keyword search interface is now present. It indexes OCR text and metadata in memory/application space and provides a future boundary for Postgres full-text search and pgvector. No fake embeddings are generated.

## Still future / experimental

- production-grade automatic backend scoring across multiple engines
- advanced layout/table/stamp/signature detection
- handwriting recognition
- semantic/vector retrieval using real embeddings
- large reviewed Bihar corpus
- field-level accuracy dashboards
- OCR-VL integration

These are intentionally documented as future work, not claimed as completed.
