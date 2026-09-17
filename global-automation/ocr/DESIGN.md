# Government Document Vision & OCR Platform (GovDoc Vision) — Design & Upgrade Guide

## Naming convention

- **Canonical product name:** Government Document Vision & OCR Platform
- **Short product name:** GovDoc Vision
- **Engineering shorthand:** Global OCR
- **Package:** `global-automation/ocr/`

“Global OCR” is retained as an engineering shorthand for continuity, but GovDoc Vision is the canonical name for architecture, documentation, releases, and future integrations.

## Purpose
Reusable OCR and document-understanding layer for Indian government documents. The first language/domain pack is Bihar Education; the architecture is intentionally extensible to Bihar Government, other states, and Central Government.

## Separation boundary
`global-automation/ocr/` is shared infrastructure. It must not depend on a consuming project's database, storage, Telegram bot, portal, credentials, or approval workflow. Projects integrate through `ocr_service.py` rather than copying OCR rules.

## Current pipeline
1. Consumer supplies a local PDF to the public OCR service.
2. `ocr_engine.py` first attempts embedded PDF text.
3. If embedded text is insufficient, PDF pages are rendered with `pdftoppm` and OCR runs with Tesseract Hindi + English.
4. `preprocess.py` can apply a conservative document profile to rendered images while preserving the original.
5. `correction.py` applies conservative whitespace, label, and date-format corrections.
6. `sarkari_normalizer.py` extracts metadata and canonicalizes known authority/date values.
7. `subject_extractor.py` handles multi-line subjects and stops at common administrative/footer labels.
8. Government Document Intelligence extracts evidence-backed authority, subject, document type, actions, deadlines and short description.
9. `ocr_service.py` calculates evidence-backed metadata quality and returns text, metadata, method, filename, and service version.

Storage/intake/publication systems remain outside this package.

## Image preprocessing
The shared preprocessing layer currently provides a conservative `document` profile using grayscale, autocontrast, and a mild median filter. The original image is never overwritten. A `none` profile is available for consumers that need untouched input.

Do not add aggressive thresholding, sharpening, deskew, or rotation correction as defaults without representative Hindi-document tests; Devanagari matras and thin strokes can be damaged by over-processing.

## Quality scoring
Confidence is quality-based rather than a simple count of populated fields. Each core field is checked for basic validity and whether its extracted value is present in OCR evidence. Current weights: subject 30%, authority 30%, reference 15%, issue date 25%.

- `HIGH`: score >= 0.80
- `MEDIUM`: score >= 0.45
- `LOW`: score < 0.45

This is an extraction-quality signal only, never an approval/publication decision.

## Backend architecture
`backend.py` defines the reusable backend contract. Tesseract is the current implementation. Future local/open backends must implement the same interface and pass regression tests plus benchmark comparison before becoming the default.

## Design principles
- Never invent a missing field.
- Preserve source wording whenever possible.
- Separate OCR, preprocessing, correction, extraction, classification, and publication.
- Keep storage and OCR independently replaceable.
- Keep government-domain dictionaries in language packs.
- Prefer deterministic rules before adding a model.
- Every new correction should become a regression test.
- Keep public service contracts backward compatible where practical.

## Upgrade loop
`real document → OCR sample → identify error → add reusable correction/extractor → regression case → CI → benchmark → release`

Do not silently alter expected values to make a failing test pass.

## Public integration contract
```python
from ocr.ocr_service import process_file
result = process_file("document.pdf", "work")
```

Result fields include `text`, `subject`, `authority`, `reference_number`, `issue_date`, `office`, `department`, `category`, `confidence`, `confidence_details`, `extraction_method`, `filename`, and `ocr_service_version`. Missing values remain `None`.

## Future upgrades checklist
- [x] Date normalization and validation baseline.
- [x] Authority alias normalization baseline.
- [x] Multi-line subject extraction baseline.
- [x] Shared correction layer.
- [x] Quality-based confidence baseline.
- [x] Pluggable backend contract.
- [x] Conservative image preprocessing baseline.
- [x] Government Document Intelligence baseline.
- [ ] Add real Bihar Education OCR samples with provenance.
- [ ] Add page-level OCR diagnostics.
- [ ] Add document-type taxonomy versioning.
- [ ] Benchmark every backend against the same corpus with extraction accuracy.
- [ ] Add advanced deskew/rotation only after benchmark evidence.
- [ ] Add structured error diagnostics without exposing document content.
- [ ] Publish a migration note before changing the default backend.
