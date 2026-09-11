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
    build_reference_timeline, SQLiteSearchStore, SupabaseSearchStore,
    SearchFilter, SearchStore, search_with_filter,
    ClusterSearchQuery, search_clusters,
    extract_evidence_relations, check_runtime,
    build_release_manifest, verify_release_manifest,
    OCRPlatformError, emit_event, backup_sqlite, restore_sqlite,
)
```

## Architecture

```text
Government Document → OCR text + geometry → Structure/Sections/Tables
        → Multi-page Structure Graph → Intelligent Reconstruction
        → Document Understanding Graph → Global Search Index
        → Cross-Document Graph → Candidate Clusters → Reference Timeline
        → Persistent Search Contract → SQLite / Supabase Adapter → Consumer project
                                      ↓
                         Golden Search Regression Gate
                                      ↓
                     Release Manifest + Operations + DR
```

**Evidence rule:** derived output retains source block IDs, entity IDs, document IDs and page provenance. Original OCR evidence is never rewritten; reconstruction, search, clustering and cross-document intelligence never invent source content.

## P26–P28

P26 provides an optional Supabase/Postgres persistence adapter with RLS-safe schema. P27 combines explicit candidate clusters with explicit parsed timeline dates. P28 provides a sanitized golden retrieval regression gate. These are frameworks and tests; no benchmark or production pass is claimed until actually executed in the target environment.

## P29 — Packaging, versioning and release integrity

`release_manifest.py` defines a dependency-free semantic-versioned release manifest. Selected release files are sorted deterministically and recorded with size + SHA-256. `verify_release_manifest()` fails closed on missing, changed, or path-escaping files.

Large model binaries remain outside Git when appropriate; releases must reference controlled artifacts by immutable version/digest rather than `latest`. The manifest is evidence of what was released, not proof that CI passed.

## P30 — Structured errors + observability

`errors.py` provides stable machine-readable error codes for invalid input, backend availability/failure, storage, resource, configuration and release-integrity failures. Consumers can handle `OCRPlatformError` without parsing free-form exception strings.

`observability.py` provides JSON-safe operation events with duration/status and non-sensitive fields. Source document text, OCR payloads and credentials must never be placed in event fields. The core remains framework/logging-provider independent.

## P31 — Backup, restore and disaster recovery

`backup.py` provides consistent SQLite backup, SQLite integrity verification and atomic restore. Restore first verifies the source backup, restores into a temporary file, verifies the restored database, then atomically replaces the destination.

Backups must be stored separately from the live database and tested periodically by restoring to an isolated destination. A successful backup operation alone is not a disaster-recovery certification; operational retention, off-host copies, access controls and restore drills remain deployment responsibilities.

## Search evolution / production hardening path

```text
P22 SQLite persistence
P23 Search contract + filters
P24 Explicit evidence relations
P25 Runtime health
P26 Supabase/Postgres adapter
P27 Cluster-aware search + timeline
P28 Golden regression gate
P29 Release manifest + integrity
P30 Structured errors + observability
P31 Backup/restore + DR
P32 Resource limits/concurrency/timeouts
P33 Artifact verification + controlled releases
P34 Full production certification gate
```

## Implemented production-hardening modules

- `release_manifest.py` — deterministic release inventory and SHA-256 verification.
- `errors.py` — stable platform error taxonomy.
- `observability.py` — structured, privacy-safe operation events.
- `backup.py` — SQLite backup, integrity check and atomic restore.

## Production gate

The platform is architecturally production-oriented but **not yet production-certified**. Certification requires actual repository CI/full regression execution, verified backend/runtime compatibility, representative Hindi/mixed-language golden data, deployment-specific persistence validation, backup/restore drills, resource-limit testing and controlled artifact verification.

No CI pass, OCR accuracy claim, benchmark pass, disaster-recovery certification or production certification is inferred merely from code presence.

## Recovery checklist

1. Read this README.
2. Confirm canonical branch `feature/global-ocr-platform` and PR #6.
3. Inspect latest commit and changed files.
4. Run the complete OCR/search test suite in the target environment.
5. Run `check_runtime()` with deployment-required backends enabled.
6. Verify the release manifest before deployment.
7. Back up persistent search data and perform an isolated restore drill.
8. Preserve original source files and all page/block/entity provenance.
9. Record every material production decision here immediately after implementation.
