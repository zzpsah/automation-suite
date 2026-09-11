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
- Bihar education domain vocabulary and OCR-alias detection
- storage-neutral keyword search interface
- compatibility-oriented service API

The School Document Pipeline remains outside this package and continues to own storage, Supabase lifecycle, publication and Telegram operations.

## Intelligence engine

Government intelligence is evidence-first. It prioritizes header authority, labelled official subject, document-type evidence, actionable instructions and source dates. Missing evidence stays missing; OCR confidence is not publication approval.

## Bihar language-pack improvement — v0.3.0

The Bihar pack is now a two-layer vocabulary system:

1. `bihar_districts.json` — district, office and school identity vocabulary.
2. `bihar_education.json` — Bihar education administration, school types, academic terms, staff/service terms, infrastructure, welfare, document labels, common OCR aliases and conservative Unicode normalization.

The resolver now:

- normalizes safe Unicode variants before matching
- detects education-domain terms with source evidence
- detects known OCR aliases without silently rewriting source text
- returns canonical district/office keys only when evidence is present
- marks multiple district/office candidates as ambiguous instead of guessing
- explicitly refuses to infer district/block from a person's name
- exposes `source_text_preserved=true` for downstream consumers

### Real-document feedback

A real Bihar school infrastructure form containing printed Hindi, handwritten Hindi answers, numeric fields, a table and a signature/stamp was supplied as a stress-test sample. It showed that printed OCR and vocabulary matching are useful, while handwritten text and table/field association remain weaker areas.

The sample therefore becomes a target for future regression coverage, especially:

- handwritten Hindi recognition
- question-to-answer/table association
- numeric field extraction
- uncertain handwriting marking
- school infrastructure terminology

The engine must not turn an uncertain handwritten reading into a confident invented value.

## Bihar language-pack improvement plan

The next corpus-driven additions should focus on reviewed Bihar government documents rather than arbitrary word lists:

1. BSEB/OFSS admission and examination terminology
2. DEO/BEO/DPO/RDD and block-level office terminology
3. district/block aliases and spelling variants
4. school and UDISE terminology
5. Hindi administrative labels and OCR variants
6. dates, reference-number labels and common document types
7. infrastructure/survey vocabulary from real school forms
8. reviewed handwritten examples, stored as corrections/evidence rather than blind replacements

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
