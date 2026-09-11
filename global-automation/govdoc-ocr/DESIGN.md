# GovDOC OCR Engine — Design & Upgrade Guide

## Identity

**GovDOC OCR Engine** is the shared OCR and document-understanding layer for Indian government documents. The first language/domain pack is Bihar Education; the architecture is intentionally extensible to Bihar Government, other states, and Central Government.

## Scope boundary

This package is a **shared OCR foundation**, not a school-specific document processor. It must remain usable by future projects without requiring Telegram, Supabase, Backblaze B2, Google Drive, or any particular database schema.

Project-specific workflows should call `ocr_service.py`. Storage, intake, publication, portal automation, and business rules belong outside this package.

## Stable consumer interface

Use:

```python
from ocr.ocr_service import process_pdf
result = process_pdf(pdf_path, work_dir)
```

The result contains extracted text, structured government-document metadata, extraction method, filename, and OCR service version. Consumers should tolerate missing metadata fields and must not treat OCR output as authoritative without appropriate validation.

`ocr_service.py` is the compatibility boundary. Internal engine modules may evolve while this public interface remains stable where practical.

## Current pipeline

1. A consumer supplies a PDF to the shared OCR service.
2. The OCR engine first attempts embedded PDF text.
3. If embedded text is insufficient, PDF pages are rendered and OCR runs with Tesseract Hindi + English.
4. Normalization performs conservative cleanup and metadata extraction.
5. The shared service returns text + metadata to the calling project.
6. A project-specific processor may persist, classify further, publish, or automate a portal action.

For the current school document pipeline, object storage and Supabase remain outside this package.

## Current feature set

- Hindi + English OCR.
- Embedded PDF text extraction.
- Scanned PDF OCR.
- Conservative text cleanup/normalization.
- Government-document field extraction.
- Bihar Education language/domain foundation.
- Regression corpus and deterministic correction rules.
- OCR confidence information.
- Service versioning and compatibility boundary.
- Replaceable backend design.

## Metadata contract

The reusable extractor currently exposes:
`subject`, `authority`, `reference_number`, `issue_date`, `office`, `department`, `category`, `confidence`.

The service additionally returns:
`text`, `extraction_method`, `filename`, `ocr_service_version`.

Future fields should be added backward-compatibly, with tests and documentation. Downstream consumers must tolerate missing values.

## Design principles

- Never invent a missing field.
- Preserve source wording whenever possible.
- Separate raw OCR, normalization, extraction, classification, and publication.
- OCR confidence is not publication approval.
- Keep storage and OCR independently replaceable.
- Keep government-domain dictionaries in language packs, not hard-coded into storage code.
- Prefer deterministic rules before adding a model.
- Every new correction should become a regression test.
- Do not copy OCR logic into downstream projects; reuse the shared service.
- Keep the public service contract independent of infrastructure.

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

A backend upgrade must not require consumers to rewrite their integration if the stable service contract can be preserved.

## Versioning and compatibility

- Keep `process_pdf()` stable where practical.
- Add fields backward-compatibly.
- Avoid coupling the OCR package to Supabase, Telegram, B2, or Google Drive.
- Document breaking changes in this file and in the repository changelog/PR.
- Keep CI tests independent from private credentials.
- Increment the service version when the consumer contract changes materially.
- Keep backend selection internal to the service where practical.

## Future upgrades checklist

- [ ] Add real Bihar Education OCR samples with provenance.
- [ ] Add date normalization and validation tests.
- [ ] Add authority alias map for Bihar districts/blocks.
- [ ] Add multi-line subject extraction tests.
- [ ] Add page-level OCR diagnostics.
- [ ] Add confidence scoring based on field quality, not only field count.
- [ ] Add pluggable OCR backend interface behind `ocr_service.py`.
- [ ] Add image input support without breaking PDF consumers.
- [ ] Add DOCX/scanned-image adapters where justified.
- [ ] Add document-type taxonomy versioning.
- [ ] Benchmark every backend against the same corpus.
- [ ] Add benchmark reports for accuracy, latency, and resource usage.
- [ ] Publish a migration note before changing the default backend.
- [ ] Add compatibility tests for every consumer-facing service change.
- [ ] Add examples for new projects integrating the shared service.
