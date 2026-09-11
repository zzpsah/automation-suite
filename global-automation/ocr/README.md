# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints, limitations and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import process_file, process_pdf, process_image, reconstruct_document, reconstruct_markdown, build_cross_document_graph
```

## Architecture

```text
Government Document → OCR text + geometry → Structure/Sections/Tables
        → Multi-page Structure Graph → Intelligent Reconstruction
        → Document Understanding Graph → Cross-Document Graph → Consumer project
```

**Evidence rule:** derived output retains source block IDs, entity IDs, document IDs and page provenance. Original OCR evidence is never rewritten; reconstruction and cross-document intelligence never invent source content.

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

## P19 — Cross-document intelligence

`cross_document.py` provides the first conservative cross-document graph layer. It accepts multiple P18 `DocumentUnderstandingGraph` objects keyed by stable document IDs and creates relationships only from **exact normalized entity-value matches** across different documents.

Supported baseline relationships:

- `shared_reference` — exact normalized reference entity match.
- `shared_contact` — exact normalized email entity match.
- `shared_authority` — exact normalized authority entity match.

Normalization is limited to surrounding whitespace, repeated whitespace and Unicode-aware case folding. Original entity values and IDs remain untouched.

P19 deliberately does **not** infer same-case identity, chronology, causality, legal supersession, or document relationships from dates alone. Every relation retains source/target document IDs, source/target entity IDs, confidence and a deterministic evidence reason.

## Implemented modules

- `document_structure.py` — explicit page/block structure.
- `reading_order.py` — deterministic geometry-aware reading order.
- `section_intelligence.py` — explicit section/annexure/attachment boundaries.
- `table_schema.py` — evidence-preserving structured table schema.
- `structure_graph.py` — adjacent-page continuation and entity-continuity graph.
- `intelligent_reconstruction.py` — source-traceable graph-aware reconstruction.
- `document_understanding.py` — conservative semantic entities and graph relations.
- `cross_document.py` — conservative exact-match cross-document relations.

## Release status

P19 implementation, public API export and regression tests are committed. **Production certification is not claimed** until repository CI and broader structure/semantic benchmarks complete successfully.

## Roadmap

1. Complete graph-aware reconstruction with richer Markdown/HTML/JSON table rendering while preserving evidence.
2. Upgrade table detection for merged/irregular cells and explicit row/column geometry.
3. Upgrade reading order to graph-based global optimization.
4. Expand validated Bihar government entity/field extraction.
5. Build reviewed corpus and structure/semantic golden benchmarks.
6. Calibrate confidence and release policy.
7. Add validated optional vision/VLM backends.
8. Expand P19 with explicit textual relationship markers such as “in continuation of” and “supersedes”, only when directly evidenced.
9. Add persistent cross-document indexing, clustering and query APIs after single-document gates pass.
