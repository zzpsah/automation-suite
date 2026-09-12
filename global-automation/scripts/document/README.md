# School Document Pipeline

Production document ingestion, storage, OCR, metadata extraction, publication and monitoring for the UMV Tetahali School Document Pipeline.

> **Boundary:** Telegram/Supabase/B2/Drive remain the transport and storage layers. GovDOC Vision is the canonical OCR and government-document intelligence engine for the document-processing path. The existing pipeline remains responsible for lifecycle, metadata persistence and publication.

## Production architecture

```text
Telegram / Drive intake
        |
        v
Supabase Intake (`telegram_intake`)
        |
        v
Backblaze B2  ---------------- PRIMARY FILE STORAGE
        |
        +--------------------> Google Drive -------- BACKUP / DELIVERY
        |
        v
SHA-256 verification
        |
        v
GovDOC Vision OCR
        |
        +--> embedded PDF text when reliable
        +--> rendered document OCR when needed
        +--> image OCR for Telegram photos
        +--> Hindi + English reconstruction / normalization
        +--> geometry-aware line reconstruction
        |
        v
Metadata + OCR provenance
        |
        v
Supabase `documents`
        |
        +--> duplicate detection
        +--> context-aware filename
        |
        v
Publication Worker
        |
        v
Public archive
```

### Responsibilities

| Component | Role |
|---|---|
| Telegram | Input/transport only |
| Supabase | Durable metadata/state/control plane |
| Backblaze B2 | Primary file storage |
| Google Drive | Backup + public delivery source |
| GovDOC Vision | OCR, OCR reconstruction and government-document intelligence |
| Internal Document Processor | Lifecycle orchestration, persistence and publication metadata |
| Publication Worker | Safe automatic publication |
| Drive Filename Sync | Human-readable Drive names from Supabase metadata |
| Health Monitor | Detect structural inconsistencies |
| Recovery Diagnostics | Identify stale/failed records for recovery |
| GitHub Actions | Scheduled execution and automation |

**No R2 is used.** Storage remains B2 primary + Google Drive backup.

## Telegram → Storage

The Telegram/Supabase path records incoming documents in `telegram_intake`. The global storage worker:

1. downloads the Telegram file,
2. calculates SHA-256,
3. writes B2 as primary,
4. writes Google Drive as backup,
5. verifies the stored object,
6. records storage metadata in Supabase.

Expected successful storage state:

```text
telegram_intake.status = Stored
storage.b2_status      = AVAILABLE
storage.drive_status   = AVAILABLE
storage.verified       = true
```

## Document processing

Implementation: `document_processor.py` with the GovDOC adapter entrypoint `document_processor_with_govdoc.py`.

Workflow: `.github/workflows/global-document-processor.yml`

Processing sequence:

```text
Verified B2 object
      ↓
Download
      ↓
GovDOC Vision
      ↓
Embedded text when reliable / image or rendered-page OCR when needed
      ↓
Hindi + English cleanup and line reconstruction
      ↓
Subject / authority / reference / date / category
      ↓
OCR provenance + confidence
      ↓
Checksum duplicate check
      ↓
Supabase documents
```

### OCR quality contract

The OCR output should be treated as structured document text, not as a raw character dump. In particular:

- preserve meaningful line and paragraph boundaries,
- reconstruct lines from OCR geometry where available,
- keep Hindi and English text intact without unnecessary transliteration,
- preserve dates, reference numbers and numbered items,
- avoid merging unrelated columns or form fields into a single paragraph,
- normalize repeated whitespace and OCR artefacts without changing document meaning,
- expose OCR engine/backend/version and extraction method as provenance,
- distinguish a genuine GovDOC result from any legacy/degraded fallback.

For images, the production adapter detects the image format and routes it directly through GovDOC image processing rather than treating it as a PDF. This is important for Telegram photos.

## Context-aware filenames

Every processed document keeps both names:

```text
original_filename = Telegram/source name
                     ↓
display_filename  = generated contextual name
```

The original filename remains available for audit. The B2 storage key is intentionally stable and is not renamed during this operation.

## Duplicate protection

The processor uses the stored SHA-256 checksum to detect an already-ingested file. A duplicate is linked to the existing document instead of creating another normal document record.

## Publication

Normal publication requires a completed, useful, non-sensitive, non-duplicate document with sufficient extraction confidence and a meaningful subject. Publication records its public URL, approval state, timestamp and revision.

The public archive must show a short meaningful subject rather than a giant OCR paragraph or generic `Document`/`Letter` fallback when useful metadata exists.

## Monitoring and recovery

### Health monitor

`pipeline_health.py` performs read-only consistency checks across intake and document states.

### Recovery diagnostics

`pipeline_recovery.py` identifies stale `Received`, `Stored`, storage-failure and processing-failure records that may be recoverable by the existing workers. It is deliberately diagnostic and non-mutating.
