# Global Sarkari OCR — Design & Upgrade Guide

## Purpose
Reusable OCR and document-understanding layer for Indian government documents. The first language/domain pack is Bihar Education; the architecture is intentionally extensible to Bihar Government, other states, and Central Government.

## Separation boundary
`global-automation/ocr/` is shared infrastructure. It must not depend on a consuming project's database, storage, Telegram bot, portal, credentials, or approval workflow. Projects integrate through `ocr_service.py` rather than copying OCR rules.

## Current pipeline
1. Consumer supplies a local PDF to the public OCR service.
2. `ocr_engine.py` first attempts embedded PDF text.
3. If embedded text is insufficient, PDF pages are rendered with `pdftoppm` and OCR runs with Tesseract Hindi + English.
4. `correction.py` applies conservative whitespace, label, and date-format corrections.
5. `sarkari_normalizer.py` extracts metadata and canonicalizes known authority/date values.
6. `subject_extractor.py` handles multi-line subjects and stops at common administrative/footer labels.
7. `ocr_service.py` calculates evidence-backed metadata quality and returns text, metadata, method, filename, and service version.

Storage/intake/publication systems remain outside this package.

## Quality scoring
Confidence is now quality-based rather than a simple count of populated fields. Each core field is checked for basic validity and whether its extracted value is present in the OCR evidence. The current weights are subject 30%, authority 30%, reference 15%, and issue date 25%.

- `HIGH`: score >= 0.80
- `MEDIUM`: score >= 0.45
- `LOW`: score < 0.45

This score is an extraction-quality signal only. It is not an approval or publication decision. Future versions may add field-specific validators without changing the public contract.

## Design principles
- Never invent a missing field.
- Preserve source wording whenever possible.
- Separate OCR, correction, extraction, classification, and publication.
- OCR confidence is not publication approval.
- Keep storage and OCR independently replaceable.
- Keep government-domain dictionaries in language packs, not hard-coded into storage workers.
- Prefer deterministic rules before adding a model.
- Every new correction should become a regression test.
- Backward-compatible public service contracts are preferred.

## Training / improvement strategy
This project is rule-and-corpus driven rather than claiming model training from a small local dataset. Improvement happens through a growing labelled corpus of real document text and expected metadata.

### Upgrade loop
`real document → OCR sample → identify error → add correction/extractor → add regression case → CI → benchmark → release`

Do not silently alter expected values to make a failing test pass. Review the source document first.

## Public integration contract
Consumers should use:
```python
from ocr.ocr_service import process_file
result = process_file("document.pdf", "work")
```

The result includes `text`, `subject`, `authority`, `reference_number`, `issue_date`, `office`, `department`, `category`, `confidence`, `confidence_details`, `extraction_method`, `filename`, and `ocr_service_version`. Missing values remain `None`.

## Future OCR backends
Tesseract is the current free baseline and must remain supported. Future backends may include PaddleOCR, OCR-VL models, or another local/open model. New backends should implement the same text-extraction contract and be evaluated against the corpus before becoming the default.

## Versioning and compatibility
- Keep public function names stable where practical.
- Add fields backward-compatibly.
- Avoid coupling the OCR package to Supabase, Telegram, B2, Google Drive, or any school-specific application.
- Document breaking changes in `DESIGN.md` and `CHANGELOG.md`.
- CI tests must remain independent from private credentials.
- Increment `OCR_SERVICE_VERSION` when the public result contract or extraction semantics materially change.

## Operational safeguards
- Never commit API tokens, refresh tokens, service-role keys, or storage keys.
- Tesseract binaries are runtime dependencies, not repository assets.
- Preserve original OCR evidence in consuming systems; corrected text is a derived representation.
- Text-only intake records must not be treated as PDF OCR jobs by consumers.

## Future upgrades checklist
- [x] Date normalization and validation baseline.
- [x] Authority alias normalization baseline.
- [x] Multi-line subject extraction baseline.
- [x] Shared correction layer.
- [x] Quality-based confidence baseline.
- [ ] Add real Bihar Education OCR samples with provenance.
- [ ] Add page-level OCR diagnostics.
- [ ] Add pluggable OCR backend interface.
- [ ] Add document-type taxonomy versioning.
- [ ] Benchmark every backend against the same corpus.
- [ ] Add image preprocessing profiles for noisy scans.
- [ ] Add structured error diagnostics without exposing sensitive document content.
- [ ] Publish a migration note before changing the default backend.
