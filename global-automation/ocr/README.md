# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints, limitations and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import process_file, process_pdf, process_image, reconstruct_document, reconstruct_markdown
```

## Architecture

```text
Government Document → OCR text + geometry → Structure/Sections/Tables
        → Multi-page Structure Graph → Intelligent Reconstruction
        → Document Understanding Graph → Consumer project
```

**Evidence rule:** derived output retains source block IDs and page provenance. Original OCR evidence is never rewritten; reconstruction only joins explicitly linked blocks and never invents content.

## P17 — Intelligent reconstruction

`intelligent_reconstruction.py` provides `ReconstructedBlock`, `ReconstructedDocument`, `reconstruct_document()`, `reconstruct_markdown()` and `reconstructed_to_dict()`.

The baseline is deliberately conservative:

- explicit P16 `continuation` edges join cross-page blocks
- source block IDs are retained as `source_block_ids`
- page numbers and block types are preserved
- headers and footers remain structural blocks and are omitted from Markdown presentation
- headings/section-like blocks can render as Markdown headings without changing their wording
- table blocks remain untouched rather than being fabricated into cells
- JSON serialization preserves reconstruction provenance

No reconstruction decision is treated as semantic or legal truth.

## P16 — Multi-page structure graph

`structure_graph.py` provides deterministic adjacent-page continuation and entity-continuity edges using explicit blocks, boundaries, token overlap and similarity. It preserves source evidence.

## P18 — Document understanding graph

`document_understanding.py` provides conservative reference/date/email/authority entities and relations derived only from recognized source text and supplied structure-graph edges.

## Implemented modules

- `document_structure.py` — explicit page/block structure.
- `reading_order.py` — deterministic geometry-aware reading order.
- `section_intelligence.py` — explicit section/annexure/attachment boundaries.
- `table_schema.py` — evidence-preserving structured table schema.
- `structure_graph.py` — adjacent-page continuation and entity-continuity graph.
- `intelligent_reconstruction.py` — source-traceable graph-aware reconstruction.
- `document_understanding.py` — conservative semantic entities and graph relations.

## Release status

P17 implementation and regression tests are committed, but **production certification is not claimed** until the repository CI run completes successfully and broader document reconstruction benchmarks are executed.

## Roadmap

1. Complete graph-aware reconstruction with richer Markdown/HTML/JSON table rendering while preserving evidence.
2. Upgrade table detection for merged/irregular cells and explicit row/column geometry.
3. Upgrade reading order to graph-based global optimization.
4. Expand validated Bihar government entity/field extraction.
5. Build reviewed corpus and structure/semantic golden benchmarks.
6. Calibrate confidence and release policy.
7. Add validated optional vision/VLM backends.
8. Expand cross-document intelligence after single-document gates pass.
