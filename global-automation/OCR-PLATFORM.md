# Global OCR Platform

Global Sarkari OCR and Global Document Processing are reusable platform products. School Document Pipeline is a consumer, not an owner of OCR training.

## Architecture

```text
                         GLOBAL OCR PLATFORM
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
       GLOBAL OCR ENGINE                 DOCUMENT ENGINE
             │                                   │
     ┌───────┼────────┐                 ┌────────┼─────────┐
 Tesseract PaddleOCR Future VLM      Extraction Metadata Classification
             │                                   │
             └───────────────┬───────────────────┘
                             ▼
                    Validated OCR Release
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       School             Telegram         Future Projects
       Pipeline
```

## Product contracts

### Global OCR Engine
Input: PDF/image. Output: source-preserving OCR text, page text where available, backend/method information, confidence and privacy-safe diagnostics.

Public consumer entry points remain `ocr.process_file()` and `ocr.process_pdf()` via `ocr_service`; consumers must not depend on backend internals.

### Global Document Processing Engine
Input: a file. Output: OCR evidence plus derived subject, authority, reference, date, document type/category, summary, entities and confidence. Its public entry point is `document_engine.process(file, work_dir)`.

## Training boundary

```text
Production projects → feedback/corrections/errors → Global OCR Training
                                      ↓
                             candidate + benchmark
                                      ↓
                              human/code review
                                      ↓
                              validated release
                                      ↓
                              all consumers
```

Training never runs inside School Document Pipeline and never silently edits production runtime behavior.

## Backend boundary

Tesseract, PaddleOCR and future VLMs are adapters. They are not the training system. Backend changes require the same stable interface, tests, benchmarks and explicit release/versioning.

## Artifact boundary

Source, adapters, language packs, manifests, tests and documentation live in Git. Large model binaries live in controlled release artifacts and are referenced by immutable version + SHA-256. Production rejects unpinned `latest` artifacts and checksum mismatches.

## Safety

No component may invent official names, dates, references, authorities or actions. Original OCR evidence remains available. Publication/approval decisions belong to consuming applications, not OCR/document understanding.
