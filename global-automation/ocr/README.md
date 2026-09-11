# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints, limitations and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import process_file, process_pdf, process_image

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
 ├── Tesseract
 ├── PaddleOCR
 └── Future VLM
        ↓
OCR text + geometry
        ↓
Region Alignment / Consensus
        ↓
Document Structure Intelligence
 ├── explicit blocks
 ├── global reading order
 ├── columns
 ├── headers / footers
 ├── sections / annexures / attachments
 └── explicit table schema
        ↓
Multi-page Structure Graph (next)
        ↓
Visual Artifact Intelligence
        ↓
Layout-preserving Reconstruction
        ↓
Document Understanding
        ↓
Consumer project
```

**Important:** OCR must not simply flatten a government document into a text blob. The target representation is **OCR → geometry → layout blocks → document structure → optimized reading order → structured sections/tables → formatted text/HTML/Markdown/JSON**. Original evidence remains preserved.

## P14 — Global reading order

`reading_order.py` provides `ReadingOrderBlock` and `optimize_reading_order()`.

The current optimizer is deterministic and conservative:

1. process pages in numeric order
2. emit detected headers first
3. order body blocks top-to-bottom within explicit columns
4. infer visual column bands when columns are not explicitly assigned
5. emit footers last
6. use stable geometry/block IDs as tie-breakers

This is a structure/routing heuristic, not semantic or legal truth. Source OCR and page evidence remain unchanged.

## P15 — Sections, annexures, attachments and tables

`section_intelligence.py` adds explicit boundary signals for clearly marked:

- sections
- annexures / appendices
- attachments / enclosures

Detection is intentionally textual and conservative. It reports a `SectionBoundary` with page, source block, marker label and confidence. It does **not** invent a boundary merely because a document appears to change topic.

`table_schema.py` adds an explicit `StructuredTable` / `StructuredTableCell` representation over already detected OCR cells. It preserves source coordinates and text and supports `row_span` / `column_span` fields for future merged/irregular-cell detection without fabricating missing cells. The current detector remains conservative; the schema is ready for richer geometry-based table recognition.

## Layout intelligence

Implemented under `global-automation/ocr/`:

- `region_alignment.py` — geometry-aware OCR span alignment.
- `region_consensus.py` — region disagreement/consensus diagnostics.
- `text_reconstruction.py` — line grouping, horizontal spacing and paragraph-aware reconstruction.
- `layout_intelligence.py` — column detection and conservative table-cell detection.
- `document_structure.py` — explicit page/block structure and geometry-aware structure model.
- `reading_order.py` — deterministic global reading-order optimization.
- `section_intelligence.py` — explicit section/annexure/attachment boundary signals.
- `table_schema.py` — evidence-preserving structured table representation.

## Multi-page intelligence

`multipage_intelligence.py` provides page count, repeated-header/footer detection and continuation signals. The next structural upgrade is a graph linking sections, entities and continuation blocks across pages. Every original page remains independently addressable.

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
- layout-preserving reconstruction
- column and conservative table intelligence
- explicit document structure and global reading order
- section/annexure/attachment boundary signals
- explicit structured-table schema with merge-span fields
- signature/stamp/annotation candidate intelligence
- multi-page repeated-element intelligence
- separate image-processing benchmark foundation
- CER/WER benchmark metrics
- isolated training/improvement workflow
- DevOS recovery documentation

Not yet release-certified:

- real reviewed corpus at production scale
- calibrated benchmark results on representative Bihar government documents
- production-pinned PaddleOCR artifact
- pixel-level signature/stamp/seal vision model
- graph-based reading-order optimization beyond the current deterministic heuristic
- robust merged/irregular table detection
- full section/annexure/attachment continuity model
- cross-page entity/section continuity graph

## Release gates

A change is not considered production-ready merely because code exists. Release validation should cover unit/regression tests, image-processing regression, OCR CER/WER, Hindi + English + Sarkari terminology golden sets, field-level confidence, structure/reading-order/table/section benchmarks, backend comparison, latency/resource checks, artifact version + SHA-256 verification, consumer API compatibility, and source-evidence preservation.

Never report a gate as passed without actual execution or verified CI evidence.

## Roadmap / next recovery point

1. Build the multi-page structure graph and cross-page entity/section continuity.
2. Upgrade table detection for merged/irregular cells and explicit row/column geometry.
3. Upgrade reading order to graph-based global optimization with robust region adjacency and mixed-layout handling.
4. Add pixel-aware optional vision backend for handwriting/signature/stamp/seal detection while preserving evidence-safe routing semantics.
5. Add real reviewed Bihar Education image/PDF corpus with provenance.
6. Add CER/WER, field-level and structure-level golden benchmarks.
7. Calibrate backend confidence and release policy.
8. Add pinned PaddleOCR production artifact once benchmarked.
9. Add validated local/open VLM adapter without changing the consumer API.
10. Expand Bihar and cross-government language packs.
