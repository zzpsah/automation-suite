# GovDOC OCR → School Document Pipeline

## Status

**Integrated on `main`.** The production document-processing workflow now enters through `document_processor_with_govdoc.py`, which installs the shared GovDOC OCR Engine into the existing processor.

## What the user gets

When a stored Telegram PDF reaches document processing:

```text
Telegram PDF
   ↓
Backblaze B2 verified file
   ↓
GovDOC OCR Engine
   ↓
Hindi + English text
   ↓
Subject / authority / reference / date / category
   ↓
Existing document processor
   ↓
Supabase `documents`
   ↓
Publication + Telegram delivery
```

This means the OCR is now a shared product component instead of OCR code being owned only by the School Document Pipeline.

## Safety / fallback

The adapter only replaces OCR/text-extraction and metadata functions. Storage, duplicate detection, Supabase writes, publication eligibility and Telegram delivery remain owned by the existing pipeline.

If GovDOC OCR raises an error, the adapter falls back to the processor's existing embedded-text/Tesseract implementation. A temporary OCR improvement therefore cannot stop document processing altogether.

## Current engine

- Embedded PDF text is preferred when it contains enough usable text.
- Scanned PDFs use Tesseract Hindi + English.
- Government-document labels are extracted conservatively.
- Dates are validated before normalization.
- Missing values stay empty rather than being invented.
- Admission/BSEB classification rules are retained as deterministic rules.
- Service version is currently `2.0`.

## Important boundary

GovDOC OCR does **not** decide whether a document should be published. OCR confidence is evidence for the downstream workflow; publication remains a separate business decision.

## CI

The document pipeline test workflow now compiles both components and runs an offline GovDOC OCR metadata smoke test before the existing pipeline smoke test.

## Next upgrade

Promote the richer OCR branch capabilities (Bihar office resolver, government intelligence, taxonomy and corpus-backed corrections) into this stable `govdoc-ocr` package one capability at a time, with regression tests. Do not make production depend directly on the development branch.
