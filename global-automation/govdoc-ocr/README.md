# GovDOC OCR Engine / GovDOC Vision

Reusable OCR, image-processing and government-document intelligence engine for Indian government documents.

## Current capabilities

- PDF embedded-text extraction
- **page-level mixed PDF routing**: each page independently uses embedded text when sufficient, otherwise OCR
- scanned-PDF OCR
- Hindi + English Tesseract baseline
- optional PaddleOCR backend
- direct JPG/JPEG/PNG/TIFF/WebP image input
- conservative image preprocessing
- page-level OCR results and preprocessing diagnostics
- raw + normalized text
- versioned result envelope with `schema_version`
- evidence-based government-document intelligence
- subject, authority, document type, actions and deadlines
- Bihar district/office vocabulary foundation
- correction/normalization architecture
- storage-neutral keyword search boundary
- stable `ocr_service.py` consumer interface

## Service examples

```python
from ocr.ocr_service import process_pdf, process_image, process_document

result = process_pdf(pdf_path, work_dir)
image_result = process_image(image_path, work_dir)
any_result = process_document(path, work_dir)
```

Existing PDF consumers remain supported. New consumers can process common image formats without coupling the engine to Telegram, Supabase, B2 or Drive.

## PDF routing contract

A PDF is evaluated page-by-page. A page with at least `min_embedded_chars` non-whitespace characters uses its embedded text; sparse/empty pages are rendered and sent through the selected OCR backend. The returned `pages` array preserves page order and records `extraction_method` as either `embedded-text` or `ocr:<backend>`.

This avoids the previous whole-document decision that could incorrectly OCR a text page or skip a scanned page inside a mixed PDF.

## OCR backend policy

Tesseract Hindi + English remains the free/default baseline. PaddleOCR is optional and loaded only when selected. Future OCR-VL/local vision backends can implement the same backend contract. The engine must not require every backend for normal operation.

## Government intelligence

The intelligence layer runs after OCR/normalization and is evidence-first. It prefers explicit header authority and labelled subjects, classifies document type from source evidence, extracts actionable source lines and dates, and does not invent missing metadata. OCR confidence is never publication approval.

## Bihar language intelligence

The Bihar pack is a versioned vocabulary foundation for education/government documents. It covers administrative labels, BSEB/OFSS terminology, education offices, district aliases, school terminology and common Hindi/English variants. The pack and resolver are being expanded using reviewed real-document corrections and regression tests.

## Search boundary

`search.py` provides deterministic keyword/metadata retrieval today. It is intentionally storage-neutral and is designed to be connected later to Postgres full-text search and real pgvector embeddings. No fake semantic search is claimed.

## Architecture boundary

```text
Input PDF / Image
       ↓
Document Router
       ↓
Per-page Embedded Text OR Image Rendering + Preprocessing
       ↓
OCR Backend (Tesseract / optional PaddleOCR / future Vision)
       ↓
Raw OCR + Page Results + Provenance
       ↓
Normalization / Correction
       ↓
Government Document Intelligence
       ↓
Metadata + Evidence + Diagnostics
       ↓
Search / Calling Application
```

GovDOC owns OCR, preprocessing, normalization, language packs, intelligence, diagnostics and search interfaces. Calling applications own storage, Supabase lifecycle, publication, Telegram and business rules.

## Improvement loop

`real document → OCR → identify error → language/rule correction → regression test → benchmark → deploy`

Preserve source text and correction provenance. Do not silently rewrite raw OCR.

## Future / experimental

- stronger automatic multi-backend scoring
- advanced table/layout/stamp/signature detection
- handwriting recognition
- semantic/vector retrieval with real embeddings
- larger reviewed Bihar corpus
- OCR-VL/local multimodal models

See `docs/GOVDOC_VISION_ROADMAP.md` for the capability record and upgrade plan.
