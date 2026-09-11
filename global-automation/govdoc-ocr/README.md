# GovDOC OCR Engine

Reusable OCR and document-understanding engine for Indian government documents.

## What this is

`GovDOC OCR Engine` is the shared OCR component used by government-document automation projects in this repository.

It is **not** the School Document Pipeline itself. The pipeline can call this engine to read a PDF/image and receive OCR text plus structured government-document metadata.

## Simple product view

```text
PDF / scanned image
        |
        v
   GovDOC OCR Engine
        |
        +--> OCR text
        +--> Hindi + English recognition
        +--> cleanup / normalization
        +--> government-document field extraction
        +--> confidence information
        |
        v
Calling application / document pipeline
```

## Current capabilities

- PDF text extraction when usable text is already embedded.
- Scanned-PDF OCR using Hindi + English Tesseract.
- Conservative OCR cleanup and normalization.
- Government-document metadata extraction:
  - `subject`
  - `authority`
  - `reference_number`
  - `issue_date`
  - `office`
  - `department`
  - `category`
  - `confidence`
- Filename and extraction-method information.
- Bihar Education domain/language-pack foundation.
- Rule-and-corpus based improvement with regression tests.
- Stable consumer API through `ocr_service.py`.
- Replaceable OCR backends without forcing downstream projects to rewrite their integration.

## Stable interface

Consumers should use the shared service rather than copying OCR logic:

```python
from ocr.ocr_service import process_pdf
result = process_pdf(pdf_path, work_dir)
```

The service returns OCR text, extracted metadata, extraction method, filename, and OCR service version. Missing fields are valid and must not be invented.

## Current backend

Tesseract Hindi + English is the current free baseline. Future backends such as PaddleOCR or OCR-VL/local models may be evaluated against the same corpus before becoming a default.

## Architecture boundary

GovDOC OCR Engine owns:

- OCR
- preprocessing/normalization
- government-domain vocabulary and language packs
- metadata extraction
- OCR diagnostics and confidence
- OCR tests and benchmarks

Calling applications own:

- Telegram intake
- Supabase records
- Backblaze B2 / Google Drive storage
- publication and approval
- notifications
- portal/business rules

This separation lets the OCR engine improve independently without destabilizing production workflows.

## Project identity

- **Display name:** GovDOC OCR Engine
- **Short name:** GovDOC OCR
- **Folder:** `global-automation/govdoc-ocr/`
- **Role:** reusable OCR engine / document-understanding component

## Development branch

Active OCR development may continue on `feature/global-sarkari-ocr` until intentionally promoted to the stable branch.

## Related production system

The School Document Pipeline lives under `global-automation/scripts/document/` and may consume GovDOC OCR as a reusable component. OCR experimentation/model improvement must remain independently deployable.

## Design rules

- Never invent a missing field.
- Preserve source wording whenever possible.
- Separate raw OCR, normalization, extraction, classification, and publication.
- OCR confidence is not publication approval.
- Keep OCR independent of storage and application infrastructure.
- Prefer deterministic rules before adding a model.
- Every new correction should become a regression test.
- Text-only Telegram records are not automatically treated as PDF OCR jobs.
