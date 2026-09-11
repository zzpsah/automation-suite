# School Document Pipeline Integration Guide

## Purpose

The Government Document Vision & OCR Platform is the reusable OCR/document-processing layer. The School Document Pipeline is a consumer. Do not copy OCR logic into the school project.

## What is already available

### 1. OCR input
`process_file()` accepts PDF and common raster images. `process_pdf()` preserves page text; `process_image()` runs quality-aware OCR.

### 2. Image quality processing
Orientation normalization, bounded resize, conservative deskew, grayscale/contrast/denoise/sharpen candidates, and deterministic candidate selection are available. Original source files are not overwritten.

### 3. OCR backends
The backend abstraction supports Tesseract and an optional PaddleOCR adapter. Backend selection/benchmark helpers are available. PaddleOCR is optional and must be installed separately.

### 4. Government-document understanding
Available modules cover metadata extraction, field confidence, Hindi/government terminology normalization, Bihar office resolution, document structure, reading order, sections, tables, visual artifacts, multi-page structure, reconstruction, and explicit document-understanding entities/relations.

### 5. Cross-document intelligence
Explicit cross-document relations, candidate clusters, reference timelines, evidence relations, and cluster-aware search are available. These are evidence/grouping tools; they do not decide legal validity, authenticity, same-case identity, or causality.

### 6. Search
In-memory search and persistent SQLite/Supabase adapters are available. Search results retain document/page/block/entity provenance and support metadata filters.

### 7. Reliability / production hardening
Release manifests, SHA-256 artifact verification, structured errors, privacy-safe operation events, SQLite backup/restore, and P32 resource limits/concurrency admission are available.

## Recommended school-pipeline flow

```text
Uploaded government document
        |
        v
P32 admission checks
        |
        v
process_file()
        |
        +--> pages + text + OCR diagnostics
        |
        v
metadata / structure / confidence
        |
        v
School Pipeline business rules
        |
        v
store original + derived data + provenance
```

The school pipeline should keep the original uploaded document unchanged and store derived OCR/metadata separately. A low-confidence result should trigger the school's review path rather than silently changing source evidence.

## Minimal usage

```python
from ocr import process_file

result = process_file("document.pdf", "/tmp/ocr-work")

text = result["text"]
pages = result["pages"]
confidence = result["confidence"]
page_diagnostics = result["page_diagnostics"]
```

For images:

```python
from ocr import process_image
result = process_image("scan.jpg", "/tmp/ocr-work", language="hin+eng")
```

For a stable file-type-neutral entry point, prefer `process_file()`.

## Important output/provenance

Do not discard:
- `filename`
- `text`
- `pages[].page_number`
- `pages[].text`
- `page_diagnostics`
- `field_confidence`
- `confidence_details`
- `extraction_method`
- OCR diagnostics when supplied

Downstream extracted fields must retain their source page/block/entity IDs whenever the corresponding intelligence module provides them.

## Errors and limits

Handle `OCRPlatformError` and its specific subclasses rather than matching free-form exception strings. Apply `ResourceLimits` before expensive processing in server/queue code. The default P32 limits are intentionally conservative and configurable per deployment.

## Artifact trust

If the school deployment uses external model/runtime artifacts, verify each artifact with `ArtifactSpec` + `verify_artifact()` before loading it. Never use a floating `latest` artifact reference.

## What this layer does NOT do

It does not make school-specific approval/publication decisions, invent missing text, declare a document authentic, or determine legal validity. Those decisions remain in the consumer/business workflow.

## Integration contract

The school pipeline depends on the stable public API in `ocr/__init__.py`. Treat that API as the integration boundary. When adding new capabilities, preserve existing behavior unless a deliberate versioned change is documented.

## Recovery

Start with `global-automation/ocr/README.md`, then this file, then inspect tests and recent commits. Do not rebuild OCR logic in the school project if an equivalent platform capability already exists here.
