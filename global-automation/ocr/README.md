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
    SearchFilter, SearchStore, search_with_filter,
    extract_evidence_relations, check_runtime,
)
```

## Architecture

```text
Government Document → OCR text + geometry → Structure/Sections/Tables
        → Multi-page Structure Graph → Intelligent Reconstruction
        → Document Understanding Graph → Global Search Index
        → Cross-Document Graph → Candidate Clusters → Reference Timeline
        → Persistent Search Contract → Storage Adapter → Consumer project
```

**Evidence rule:** derived output retains source block IDs, entity IDs, document IDs and page provenance. Original OCR evidence is never rewritten; reconstruction, search, clustering and cross-document intelligence never invent source content.

## P17–P22 foundation

P17 intelligent reconstruction, P18 document understanding, P19 cross-document evidence, P20 candidate clustering, global deterministic search, P21 reference timeline and P22 SQLite persistence are implemented with tests and documented recovery boundaries.

## P23 — Search contract + metadata filters

`search_contract.py` defines the storage-neutral `SearchStore` protocol and `search_with_filter()` helper. `search_filters.py` provides deterministic filters for document ID, page, block, entity type and minimum score.

Filters operate on already-ranked `SearchHit` records and never modify source evidence. This keeps database-specific query optimization optional while preserving one consumer-facing contract.

## P24 — Explicit document relationship evidence

`evidence_relations.py` extracts only explicit textual markers such as `continuation of`, `supersedes`, and `replaces`. It returns the source block and exact evidence text plus the target reference.

These relationships are evidence signals only. They do not automatically establish legal validity, chronology, same-case identity, or authenticity.

## P25 — Runtime production health

`runtime_health.py` provides side-effect-free startup/readiness diagnostics. Required core dependencies can be enforced while Tesseract/PaddleOCR remain explicitly optional unless a deployment chooses to require them.

The health result is structured and JSON-safe, making it suitable for CLI, service readiness, deployment diagnostics and future monitoring without coupling the OCR core to a web framework.

## Search evolution path

```text
P22: SQLite persistent adapter
        ↓
P23: SearchStore contract + metadata filters
        ↓
P24: Explicit evidence relationships
        ↓
P25: Runtime health/readiness
        ↓
Supabase/Postgres adapter
        ↓
Cluster-aware query/timeline APIs
        ↓
Reviewed golden benchmarks
        ↓
Optional semantic/vector retrieval
```

## Implemented modules

- `search_filters.py` — deterministic metadata filtering.
- `search_contract.py` — storage-neutral persistent search contract.
- `persistent_search.py` — portable SQLite persistence adapter.
- `evidence_relations.py` — explicit relationship-marker extraction.
- `runtime_health.py` — read-only production runtime diagnostics.

## Production gate

The platform is architecturally production-oriented but **not yet production-certified**. Certification requires actual repository CI/full regression execution, verified backend/runtime compatibility, representative Hindi/mixed-language golden data, deployment-specific persistence validation, and operational backup/restore testing.

No CI pass, OCR accuracy claim, or production certification is inferred merely from code presence.

## Recovery checklist

1. Read this README.
2. Confirm canonical branch `feature/global-ocr-platform` and PR #6.
3. Inspect latest commit and changed files.
4. Run the complete OCR/search test suite in the target environment.
5. Run `check_runtime()` with deployment-required backends enabled.
6. Validate persistent-store backup/restore before production rollout.
7. Preserve original source files and all page/block/entity provenance.
8. Record every material production decision here immediately after implementation.
