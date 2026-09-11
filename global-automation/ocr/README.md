# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints, limitations and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import (
    process_file, process_pdf, process_image,
    reconstruct_document, reconstruct_markdown,
    build_cross_document_graph, build_candidate_clusters,
    build_search_index, DocumentSearchIndex,
)
```

## Architecture

```text
Government Document → OCR text + geometry → Structure/Sections/Tables
        → Multi-page Structure Graph → Intelligent Reconstruction
        → Document Understanding Graph → Global Search Index
        → Cross-Document Graph → Candidate Clusters → Consumer project
```

**Evidence rule:** derived output retains source block IDs, entity IDs, document IDs and page provenance. Original OCR evidence is never rewritten; reconstruction, search and cross-document intelligence never invent source content.

## P17 — Intelligent reconstruction

`intelligent_reconstruction.py` provides graph-aware reconstruction while retaining source block IDs and page provenance. Explicit continuation edges are the only cross-page join signal in the baseline.

## P18 — Document understanding graph

`document_understanding.py` provides conservative reference/date/email/authority entities and relations derived only from recognized source text and supplied structure-graph edges.

## P19 — Cross-document intelligence

`cross_document.py` accepts multiple P18 graphs keyed by stable document IDs and creates relationships only from exact normalized entity-value matches across different documents.

Supported relationships:

- `shared_reference` — exact normalized reference match.
- `shared_contact` — exact normalized email match.
- `shared_authority` — exact normalized authority match.

P19 does **not** infer same-case identity, chronology, causality, legal supersession, or document relationships from dates alone.

## P20 — Candidate clustering

`document_clustering.py` converts P19 evidence edges into deterministic **candidate clusters**. A cluster is an evidence group, **not** a claim that documents are the same legal case.

Default safety policy:

- `shared_reference` can establish a candidate cluster.
- `shared_authority` alone is too broad and does not establish a cluster.
- multiple independent supporting evidence types can establish a candidate cluster.
- relation IDs, document IDs, relation types, confidence and evidence count are retained.
- cluster IDs and ordering are deterministic.

Consumers can therefore ask for a candidate document group without embedding case-group logic in School, Telegram or portal projects.

## Global Search — reusable platform capability

`search_index.py` is intentionally **separate from P20**. Search is a platform service that every future project can consume.

The baseline `DocumentSearchIndex` supports:

- Unicode/Hindi text search
- exact entity matching
- entity containment and token-overlap matching
- document/block text matching
- deterministic relevance ordering
- configurable result limits
- page/block/entity provenance in every hit
- storage-independent indexing
- JSON-compatible serialization helpers

Example:

```python
index = build_search_index(document_graphs, blocks=source_blocks)
hits = index.search("पत्रांक 123", limit=20)
```

Every `SearchHit` retains `document_id`, `page_number`, `block_id`, match type, matched value, score and optional entity provenance. Normalization is used only for matching and never overwrites source text.

### Search evolution path

```text
Current: in-memory deterministic index
        ↓
Persistent adapter (Supabase/Postgres/SQLite)
        ↓
Metadata + field filters
        ↓
Cross-document/cluster-aware queries
        ↓
Optional semantic/vector retrieval
        ↓
Hybrid keyword + semantic ranking
```

The storage layer is deliberately not coupled to the OCR core. Future projects should persist the same search contract rather than inventing a project-specific index format.

## Implemented modules

- `document_structure.py` — explicit page/block structure.
- `reading_order.py` — deterministic geometry-aware reading order.
- `section_intelligence.py` — explicit section/annexure/attachment boundaries.
- `table_schema.py` — evidence-preserving structured table schema.
- `structure_graph.py` — adjacent-page continuation and entity-continuity graph.
- `intelligent_reconstruction.py` — source-traceable graph-aware reconstruction.
- `document_understanding.py` — conservative semantic entities and graph relations.
- `search_index.py` — reusable deterministic global document/entity search.
- `cross_document.py` — conservative exact-match cross-document relations.
- `document_clustering.py` — conservative candidate document groups from P19 evidence.

## Release status

P19, P20 candidate clustering, and the baseline global search contract have implementation/tests/documentation on the development branch. **Production certification is not claimed** until repository CI and broader structure/semantic/search benchmarks complete successfully.

## Roadmap / recovery notes

1. Run and verify the full OCR regression suite and CI after P19/P20/search changes.
2. Add persistent search adapters without coupling storage into OCR core.
3. Add structured metadata/field filters to search.
4. Expand directly evidenced cross-document relationship markers such as “in continuation of” and “supersedes”.
5. Add reviewed search golden benchmarks for Hindi, mixed-language references, OCR errors and government terminology.
6. Add case/reference timeline intelligence after search and clustering gates.
7. Add optional semantic/vector and hybrid retrieval only after deterministic search remains the evidence baseline.
8. Keep consumer projects thin: consume global OCR/search/cluster APIs; do not duplicate OCR or search business logic.
