# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints, limitations and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import process_file, process_pdf, process_image, build_understanding_graph

result = process_file("document.pdf", "/tmp/ocr-work")
result = process_file("scan.jpg", "/tmp/ocr-work")
```

Consumers receive source-preserving full text, ordered page text, diagnostics, metadata, taxonomy and confidence. Backend internals remain private.

## Architecture

```text
Government Document
        ↓
Image / Vision Processing
        ↓
OCR Backend Adapters
        ↓
OCR text + geometry
        ↓
Structure + Reading Order + Sections + Tables
        ↓
Multi-page Structure Graph
        ↓
Layout-preserving Reconstruction
        ↓
Document Understanding Graph
        ↓
Consumer project
```

**Evidence rule:** every derived structure or semantic entity is traceable to source OCR geometry/text. Original OCR evidence is never rewritten and the understanding layer does not invent missing facts.

## P17 — Intelligent reconstruction

P17 consumes structure/graph intelligence to prepare reconstruction-aware document output. Reconstruction must preserve source block IDs and page provenance while handling:

- graph-aware ordering and cross-page continuation
- section / annexure / attachment boundaries
- repeated headers and footers as structural metadata
- detected tables as structured content rather than invented prose
- source traceability from reconstructed output back to blocks/pages

Reconstruction is presentation intelligence, not a replacement for OCR evidence.

## P18 — Document understanding graph

`document_understanding.py` provides `DocumentUnderstandingGraph`, `UnderstandingEntity`, `UnderstandingRelation` and `build_understanding_graph()`.

The current conservative baseline extracts explicitly recognizable:

- reference numbers
- dates
- email addresses
- authority markers such as District Education Officer / जिला शिक्षा पदाधिकारी

When a P16 structure graph is supplied, recognized entities can inherit conservative cross-page `continuation` / `entity_continuity` relations from verified graph edges. Relations retain confidence and evidence block IDs. No semantic relationship is asserted without an upstream structural edge.

Serialization is JSON-safe through `understanding_graph_to_dict()`.

## Implemented modules

- `document_structure.py` — explicit page/block structure.
- `reading_order.py` — deterministic geometry-aware reading order.
- `section_intelligence.py` — explicit section/annexure/attachment boundaries.
- `table_schema.py` — evidence-preserving structured table schema.
- `structure_graph.py` — adjacent-page continuation and entity-continuity graph.
- `document_understanding.py` — conservative semantic entities and graph relations.

## Current implementation state

Implemented foundation:

- reusable OCR service/API
- image preprocessing and quality analysis
- Tesseract backend
- optional PaddleOCR adapter
- backend benchmark/selection policy
- multi-backend/page consensus
- line/region disagreement diagnostics
- field-aware confidence
- geometry-aware region alignment
- layout-preserving reconstruction foundation
- column and conservative table intelligence
- explicit document structure and global reading order
- section/annexure/attachment boundary signals
- explicit structured-table schema with merge-span fields
- signature/stamp/annotation candidate intelligence
- multi-page repeated-element intelligence
- multi-page structure graph
- document understanding graph baseline
- regression coverage for understanding-graph behavior
- separate image-processing benchmark foundation
- CER/WER benchmark metrics
- isolated training/improvement workflow
- DevOS recovery documentation

## Release gates

A change is not considered production-ready merely because code exists. Release validation should cover unit/regression tests, image-processing regression, OCR CER/WER, Hindi + English + Sarkari terminology golden sets, field-level confidence, structure/reading-order/table/section benchmarks, understanding-graph precision/recall on reviewed data, backend comparison, latency/resource checks, artifact version + SHA-256 verification, consumer API compatibility, and source-evidence preservation.

Never report a gate as passed without actual execution or verified CI evidence.

## Roadmap / next recovery point

1. Complete graph-aware reconstruction with source-traceable Markdown/HTML/JSON outputs.
2. Upgrade table detection for merged/irregular cells and explicit row/column geometry.
3. Upgrade reading order to graph-based global optimization with robust region adjacency and mixed-layout handling.
4. Expand understanding entities using validated Bihar government terminology and field rules.
5. Add real reviewed Bihar Education image/PDF corpus with provenance.
6. Add CER/WER, field-level, structure-level and semantic-graph golden benchmarks.
7. Calibrate confidence and release policy.
8. Add pinned PaddleOCR production artifact once benchmarked.
9. Add validated local/open VLM adapter without changing the consumer API.
10. Expand cross-document intelligence only after single-document evidence/understanding gates pass.
