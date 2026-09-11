# Global Sarkari OCR — Design & Upgrade Guide

## Purpose
Reusable OCR and document-understanding layer for Indian government documents. The first language/domain pack is Bihar Education; the architecture is intentionally extensible to Bihar Government, other states, and Central Government.

## Current pipeline
1. Input arrives through the existing Telegram/Supabase intake system.
2. Backblaze B2 is the primary object store and Google Drive is the backup.
3. `ocr_engine.py` first attempts embedded PDF text.
4. If embedded text is insufficient, PDF pages are rendered with `pdftoppm` and OCR runs with Tesseract Hindi + English.
5. `sarkari_normalizer.py` performs conservative cleanup and metadata extraction.
6. The document processor writes OCR text and structured metadata to Supabase.
7. Publication remains a separate workflow.

## Design principles
- Never invent a missing field.
- Preserve source wording whenever possible.
- Separate raw OCR, normalization, extraction, classification, and publication.
- OCR confidence is not publication approval.
- Keep storage and OCR independently replaceable.
- Keep government-domain dictionaries in language packs, not hard-coded into the storage layer.
- Prefer deterministic rules before adding a model.
- Every new correction should become a regression test.

## Training / improvement strategy
This project is rule-and-corpus driven rather than claiming model training from a small local dataset. Improvement happens through a growing labelled corpus of real document text and expected metadata.

### Corpus fields
Each JSONL case should contain:
- `name`
- `text` — representative OCR/text input
- `expected` — fields that must be extracted

### Recommended error buckets
- Devanagari character substitutions
- मात्रा/हलन्त errors
- broken words and spacing
- `विषय`, `पत्रांक`, `ज्ञापांक`, `दिनांक` label variants
- dates in `dd.mm.yyyy`, `dd/mm/yyyy`, `dd-mm-yyyy`
- Hindi/English mixed headers
- authority spelling variants (`परिषद` / `परिषद्`)
- scanned stamps/signatures/noise
- multi-line subjects
- footer/copy-to text accidentally captured as subject

### Upgrade loop
`real document → OCR sample → identify error → add normalizer/rule → add regression case → CI → deploy`

Do not silently alter expected values to make a failing test pass. Review the source document first.

## Language-pack roadmap
1. Bihar Education — current
2. Bihar Government — departments, districts, common offices
3. Other State Governments — state-specific packs
4. Central Government — ministries, departments, common office terminology
5. Cross-government common entities and document types

## Future OCR backends
Tesseract is the current free baseline and must remain a supported backend. Future backends may include PaddleOCR, OCR-VL models, or another local/open model. New backends should implement the same text-extraction contract and be evaluated against the corpus before becoming the default.

## Metadata contract
The reusable extractor currently exposes:
`subject`, `authority`, `reference_number`, `issue_date`, `office`, `department`, `category`, `confidence`.

Future fields should be added only with tests and documentation. Downstream consumers must tolerate missing values.

## Versioning and compatibility
- Keep public function names stable where practical.
- Add fields backward-compatibly.
- Avoid coupling the OCR package to Supabase, Telegram, B2, or Google Drive.
- Document breaking changes in this file and in the repository changelog/PR.
- Keep CI tests independent from private credentials.

## Operational safeguards
- Never commit API tokens, refresh tokens, service-role keys, or storage keys.
- Tesseract binaries are runtime dependencies, not repository assets.
- Failed processing must remain observable through the intake status/error metadata.
- Text-only Telegram records must not be treated as PDF OCR jobs.

## Future upgrades checklist
- [ ] Add real Bihar Education OCR samples with provenance.
- [ ] Add date normalization and validation tests.
- [ ] Add authority alias map for Bihar districts/blocks.
- [ ] Add multi-line subject extraction tests.
- [ ] Add page-level OCR diagnostics.
- [ ] Add confidence scoring based on field quality, not only field count.
- [ ] Add pluggable OCR backend interface.
- [ ] Add document-type taxonomy versioning.
- [ ] Benchmark every backend against the same corpus.
- [ ] Publish a migration note before changing the default backend.
