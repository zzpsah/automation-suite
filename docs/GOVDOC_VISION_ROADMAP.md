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
- storage-neutral keyword search interface
- compatibility-oriented service API

The School Document Pipeline remains outside this package and continues to own storage, Supabase lifecycle, publication and Telegram operations.

## Intelligence engine

Government intelligence is evidence-first. It prioritizes header authority, labelled official subject, document-type evidence, actionable instructions and source dates. Missing evidence stays missing; OCR confidence is not publication approval.

## Bihar language-pack improvement plan

The Bihar pack is being expanded around real reviewed documents rather than arbitrary word lists. Priority areas:

1. education department terminology and abbreviations
2. BSEB/OFSS admission and examination terminology
3. DEO/BEO/DPO/RDD office terminology
4. district/block aliases and spelling variants
5. school and UDISE terminology
6. Hindi administrative labels and OCR variants
7. dates, reference-number labels and common document types

Every accepted correction should become a regression case.

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
