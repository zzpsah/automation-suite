# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import (
    process_file, process_pdf, process_image,
    reconstruct_document, reconstruct_markdown,
    build_cross_document_graph, build_candidate_clusters,
    build_search_index, DocumentSearchIndex,
    build_reference_timeline, SQLiteSearchStore,
)
```

## Architecture

```text
Government Document → OCR text + geometry → Structure/Sections/Tables
        → Multi-page Structure Graph → Intelligent Reconstruction
        → Document Understanding Graph → Global Search Index
        → Cross-Document Graph → Candidate Clusters → Reference Timeline
        → Persistent Search Adapter → Consumer project
```

**Evidence rule:** derived output retains source block IDs, entity IDs, document IDs and page provenance. Original OCR evidence is never rewritten; reconstruction, search, clustering and cross-document intelligence never invent source content.

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
- serialized cluster arrays are JSON-compatible lists.

## Global Search — reusable platform capability

`search_index.py` is intentionally separate from P20. It provides Unicode/Hindi search, exact entity matching, containment/token overlap, deterministic relevance ordering, configurable limits, page/block/entity provenance, and storage-independent indexing. Normalization is used only for matching and never overwrites source text.

## P21 — Reference timeline

`reference_timeline.py` provides an evidence-only chronological view of explicitly extracted P18 `date` entities. Dates are parsed conservatively into ISO form when unambiguous; unparseable dates are retained at the end rather than discarded. References found in the same source block are attached as supporting entity IDs.

P21 does **not** decide what a date means legally or causally. It does not label a document as issued, superseded, effective, cancelled, or part of a case unless a future layer has explicit source evidence for that relationship.

## P22 — Persistent search adapter

`persistent_search.py` adds a small SQLite persistence layer while keeping the OCR/search core storage-agnostic. `SQLiteSearchStore` persists `SearchDocument` and `SearchEntity` records with deterministic indexed retrieval, upserts, provenance, and JSON-safe export.

SQLite is deliberately the first adapter because it is dependency-light and useful for local/offline deployments. **Supabase/Postgres is a future adapter, not embedded into the OCR core.** External adapters should preserve the same search contract and source provenance.

P22 does not replace the in-memory `DocumentSearchIndex`; it adds persistence for consumers that need recovery across process restarts. Search ranking remains deterministic and evidence-first.

## Search evolution path

```text
P22: SQLite persistent adapter
        ↓
Supabase/Postgres adapter (same contract)
        ↓
Metadata + field filters
        ↓
Cross-document/cluster-aware queries
        ↓
Optional semantic/vector retrieval
        ↓
Hybrid keyword + semantic ranking
```

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
- `reference_timeline.py` — conservative date/reference timeline from P18 entities.
- `persistent_search.py` — portable SQLite persistence adapter for the search contract.

## Release status

P19, P20 candidate clustering, baseline global search, P21 reference timeline, and P22 SQLite persistence have implementation/tests/documentation on the development branch. **Production certification is not claimed** until repository CI and broader structure/semantic/search benchmarks complete successfully.

## Roadmap / recovery notes

1. Verify the full OCR regression suite and CI after the current changes.
2. Add a Supabase/Postgres adapter using the P22 storage contract without coupling storage into OCR core.
3. Add structured metadata/field filters to search.
4. Expand directly evidenced cross-document relationship markers such as “in continuation of” and “supersedes”.
5. Add reviewed search golden benchmarks for Hindi, mixed-language references, OCR errors and government terminology.
6. Add cluster-aware timeline/query APIs using P20 + P21 while keeping legal meaning evidence-bound.
7. Add optional semantic/vector and hybrid retrieval only after deterministic search remains the evidence baseline.
8. Keep consumer projects thin: consume global OCR/search/cluster/timeline APIs; do not duplicate OCR or search business logic.
