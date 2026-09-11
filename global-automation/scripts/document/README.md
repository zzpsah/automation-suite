# School Document Pipeline

Production document ingestion, storage, OCR, metadata extraction, publication and monitoring for the UMV Tetahali School Document Pipeline.

> **Boundary:** this production pipeline currently uses its existing internal Tesseract OCR path. The separate Global Sarkari OCR project is being developed independently and will be integrated later through a stable interface. Do not couple this pipeline to the OCR training project.

## Quick links

- [Automation Suite](https://github.com/zzpsah/automation-suite)
- [School staging repository](https://github.com/zzpsah/umv-tetahali-staging)
- [School Public Document Archive](https://zzpsah.github.io/umv-tetahali-staging/school-document-archive.html)
- [Global Sarkari OCR — exact repository/branch](https://github.com/zzpsah/automation-suite/tree/feature/global-sarkari-ocr/global-automation/ocr)
- [Global Sarkari OCR PR #5](https://github.com/zzpsah/automation-suite/pull/5)

## School

**UCHCH MADHYAMIK VIDALAY, TETAHALI**  
**UDISE:** `10160203806`  
**Classes:** 9–12  
**BSEB College Code:** `42369`

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
        +--------------------> Google Drive -------- BACKUP
        |
        v
SHA-256 verification
        |
        v
Internal Document Processor
        |
        +--> embedded PDF text when reliable
        |
        +--> Tesseract Hindi + English OCR when needed
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
Public Drive permission + URL
        |
        v
`approved_public_documents`
        |
        v
Public School Document Archive

Independent monitoring:
  Pipeline Health + Recovery Diagnostics
```

### Responsibilities

| Component | Role |
|---|---|
| Telegram | Input/transport only |
| Supabase | Durable metadata/state/control plane |
| Backblaze B2 | Primary file storage |
| Google Drive | Backup + public delivery source |
| Internal Document Processor | Text extraction, Tesseract OCR, metadata extraction |
| Publication Worker | Safe automatic publication |
| Drive Filename Sync | Human-readable Drive names from Supabase metadata |
| Health Monitor | Detect structural inconsistencies |
| Recovery Diagnostics | Identify stale/failed records for recovery |
| GitHub Actions | Scheduled execution and automation |
| Existing Apps Script | Legacy Drive pipeline; remains intact |

**No R2 is used.** Storage remains exactly B2 primary + Google Drive backup.

## Existing Apps Script

The existing Google Apps Script pipeline is **not disabled, deleted or replaced**. Its existing Drive folders and processing remain part of the environment.

Normal processing does not require human approval. `04_Manual_Review` is reserved for genuine failures or exceptional intervention.

## Telegram → Storage

The new Telegram/Supabase path records incoming documents in `telegram_intake`. The global storage worker then:

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

Implementation: [`storage_worker.py`](../storage/storage_worker.py)  
Workflow: [`global-storage-worker.yml`](../../../.github/workflows/global-storage-worker.yml)

## Document processing

Implementation: [`document_processor.py`](./document_processor.py)  
Workflow: [`global-document-processor.yml`](../../../.github/workflows/global-document-processor.yml)

Processing sequence:

```text
Verified B2 object
      ↓
Download
      ↓
Embedded PDF text
      ↓ (if insufficient)
Render PDF
      ↓
Tesseract hin+eng
      ↓
Clean/normalize
      ↓
Subject / authority / reference / date / category
      ↓
Checksum duplicate check
      ↓
Supabase documents
```

### Current OCR

**Current production OCR = internal Tesseract Hindi + English.**

The Global Sarkari OCR project is deliberately separate. When it becomes sufficiently stable, this pipeline can consume it through a stable API rather than duplicating OCR code.

## Context-aware filenames

Every processed document keeps both names:

```text
original_filename = Telegram/source name
                     ↓
display_filename  = generated contextual name
```

Example:

```text
Spot admission extension letter.pdf
        ↓
2026-06-25_बिहार-विद्यालय-परीक्षा-समिति_सत्र-2026-28-के-लिए-स्पॉट-नामांकन.pdf
```

The original filename remains available for audit. The B2 storage key is intentionally stable and is not renamed during this operation.

Google Drive receives the human-readable `display_filename` through:

[`drive_filename_sync.py`](./drive_filename_sync.py)  
Workflow: [`global-document-drive-sync.yml`](../../../.github/workflows/global-document-drive-sync.yml)

## Duplicate protection

The processor uses the stored SHA-256 checksum to detect an already-ingested file. A duplicate is linked to the existing document instead of creating another normal document record.

This prevents repeated Telegram uploads of the exact same file from creating duplicate public archive entries.

## Publication

Implementation: [`publication_worker.py`](./publication_worker.py)  
Workflow: [`global-document-publication.yml`](../../../.github/workflows/global-document-publication.yml)

Normal publication requires a completed, useful, non-sensitive, non-duplicate document with sufficient extraction confidence and a meaningful subject. Publication records its public URL, approval state, timestamp and revision.

## Public archive

The school archive is Hindi-first and displays:

```text
Sr.No. | Letter Type | Issuing Authority | Issued Date | Upload Date | Subject | Download
```

Archive:

- [school-document-archive.html](https://github.com/zzpsah/umv-tetahali-staging/blob/main/school-document-archive.html)
- [document-archive.js](https://github.com/zzpsah/umv-tetahali-staging/blob/main/assets/document-archive.js)
- [document-archive-config.js](https://github.com/zzpsah/umv-tetahali-staging/blob/main/assets/document-archive-config.js)

The table must show a short meaningful subject, never a giant OCR paragraph or generic `Document`/`Letter` fallback when useful metadata exists.

## Monitoring and recovery

### Health monitor

[`pipeline_health.py`](./pipeline_health.py) performs read-only consistency checks across intake and document states.

Workflow: [`global-document-pipeline-health.yml`](../../../.github/workflows/global-document-pipeline-health.yml)

It checks, among other things:

- completed document missing subject,
- completed document missing Drive backup ID,
- published document missing approval/public URL,
- orphaned intake/document relationships.

### Recovery diagnostics

[`pipeline_recovery.py`](./pipeline_recovery.py) identifies stale `Received`, `Stored`, storage-failure and processing-failure records that may be recoverable by the existing workers.

It is deliberately **diagnostic and non-mutating**. It does not silently rewrite production records.

Workflow: [`global-document-recovery.yml`](../../../.github/workflows/global-document-recovery.yml)

## Failure policy

```text
Storage failure
      ↓
Storage retry

Processing failure
      ↓
Document processor retry

Publication failure
      ↓
Publication retry

Persistent/ambiguous failure
      ↓
04_Manual_Review / secure review path
```

Successful documents do not enter manual approval merely because OCR/AI enrichment was used.

Bad records are retained for audit; they are not physically deleted just because processing failed.

## Supabase data model

### `telegram_intake`

Input and storage lifecycle record.

### `documents`

Durable document metadata and processing record.

### `processing_jobs`

Processing job/attempt tracking.

### `approved_public_documents`

Safe public-facing view used by the archive.

## Important status values

### Processing

`New`, `Queued`, `Processing`, `Needs Manual Review`, `Action Required`, `Reviewed`, `Approved`, `Completed`, `Duplicate`, `Ignored`, `Archived`, `Processing Failed`

### Publication

`Unpublished`, `Published`, `Unpublished by Admin`, `Unavailable`, `Superseded`

### Priority

`URGENT`, `HIGH`, `NORMAL`, `LOW`, `IGNORE`

## Security

Never commit:

```text
SUPABASE_SERVICE_ROLE_KEY
TELEGRAM_BOT_TOKEN
B2_APPLICATION_KEY
GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN
```

They must remain GitHub/Supabase deployment secrets.

Supabase is the metadata/control plane; it is not the file store. Public access should expose only the approved public view/data required by the school archive.

## GitHub Actions

Production workflows:

- [`global-storage-worker.yml`](../../../.github/workflows/global-storage-worker.yml)
- [`global-document-processor.yml`](../../../.github/workflows/global-document-processor.yml)
- [`global-document-publication.yml`](../../../.github/workflows/global-document-publication.yml)
- [`global-document-drive-sync.yml`](../../../.github/workflows/global-document-drive-sync.yml)
- [`global-document-pipeline-health.yml`](../../../.github/workflows/global-document-pipeline-health.yml)
- [`global-document-recovery.yml`](../../../.github/workflows/global-document-recovery.yml)
- [`global-system-health.yml`](../../../.github/workflows/global-system-health.yml)

Actions dashboard: https://github.com/zzpsah/automation-suite/actions

## Tested baseline

The test document `Spot admission extension letter.pdf` successfully completed the storage → processing → publication path, including B2 primary storage, Google Drive backup, SHA-256 verification, metadata extraction and public publication.

This successful test is the baseline; future changes should preserve this path through regression/end-to-end testing.

## Development boundaries

1. Keep the existing Apps Script pipeline intact.
2. Keep B2 as primary and Google Drive as backup.
3. Do not introduce R2 into this production architecture.
4. Keep Telegram as input/transport, not permanent storage.
5. Do not make successful documents wait for human approval.
6. Use manual review only for genuine failures or exceptional cases.
7. Preserve original filenames and source provenance.
8. Use context-aware display filenames for humans.
9. Do not publish sensitive or duplicate documents.
10. Keep Global Sarkari OCR development separate until explicitly integrated.
11. Prefer safe, explainable metadata extraction over invented metadata.
12. Preserve auditability and retryability.
