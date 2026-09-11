# School Document Pipeline

Reusable production documentation for the **UMV Tetahali School Document Pipeline**.

> This README documents the production document flow. The separate Global Sarkari OCR project is a reusable OCR dependency and is intentionally documented independently.

## 1. Project

**School:** UCHCH MADHYAMIK VIDALAY, TETAHALI  
**UDISE:** `10160203806`  
**Classes:** 9–12  
**BSEB College Code:** `42369`  
**GitHub owner:** `zzpsah`

### Main repositories

- [Automation Suite](https://github.com/zzpsah/automation-suite)
- [School public/staging site](https://github.com/zzpsah/umv-tetahali-staging)
- [School main public repository](https://github.com/zzpsah/umv-tetahali)

### Live school pages

- [School homepage](https://zzpsah.github.io/umv-tetahali-staging/index.html)
- [Public Document Archive](https://zzpsah.github.io/umv-tetahali-staging/school-document-archive.html)
- [Official Documents](https://zzpsah.github.io/umv-tetahali-staging/official-documents.html)
- [Official Updates](https://zzpsah.github.io/umv-tetahali-staging/official-updates.html)
- [Notices](https://zzpsah.github.io/umv-tetahali-staging/notices.html)
- [Private Document Manager](https://zzpsah.github.io/umv-tetahali-staging/private-documents.html)
- [Secure Document Review](https://zzpsah.github.io/umv-tetahali-staging/document-review.html)
- [Admin Content](https://zzpsah.github.io/umv-tetahali-staging/admin-content.html)

---

## 2. Production architecture

```text
Telegram / Drive intake
        |
        v
Supabase Edge Function / Intake
        |
        v
Supabase `telegram_intake`
        |
        v
Backblaze B2 -------------- PRIMARY FILE STORAGE
        |
        +------------------> Google Drive ----- BACKUP
        |
        v
SHA-256 / storage verification
        |
        v
Global Document Processor
        |
        +--> embedded PDF text when reliable
        |
        +--> Tesseract Hindi + English OCR when needed
        |
        v
Supabase `documents`
        |
        v
Publication Worker
        |
        v
Google Drive public reader permission
        |
        v
`approved_public_documents`
        |
        v
Public School Document Archive
```

### System responsibilities

| Component | Responsibility |
|---|---|
| Telegram | Input/transport only |
| Supabase | Durable metadata, state, control plane |
| Backblaze B2 | Primary file storage |
| Google Drive | Backup and public delivery source |
| Document Processor | Text extraction, OCR and metadata extraction |
| Publication Worker | Safe automatic publication |
| GitHub Actions | Processing, retries, scheduled execution and monitoring |
| Apps Script | Existing legacy Drive pipeline; kept intact |
| Public archive | Human-facing document listing and downloads |

**There is no Cloudflare R2 in this architecture.** The production storage pair is B2 + Google Drive.

---

## 3. Original Apps Script pipeline

The existing Google Apps Script project remains part of the system and is **not disabled, deleted or replaced** by the new pipeline.

Existing responsibilities include Drive scanning, processing and archive handling. The operational rule is:

- `02_Processing` for active processing
- `03_Published_Archive` for published archive material
- `04_Manual_Review` only for genuine processing failures requiring intervention

Successful documents do not wait for human approval. AI/OCR enrichment is metadata assistance, not an approval gate.

---

## 4. New Telegram/Supabase intake

Bot:

- **Name:** `UMV Data Input`
- **Username:** `@UMVInputBot`
- **Authorized users:** configured in the deployment, never committed as secrets

Important commands include:

`/start` `/help` `/menu` `/text` `/document` `/photo` `/status` `/cancel` `/today` `/count` `/failed` `/search` `/doc` `/health`

Primary intake endpoint:

`https://sxfnrwugsyfypqgfglzc.supabase.co/functions/v1/telegram-input-v2`

The intake function records the incoming item in `telegram_intake`. It does not act as the long-term file store.

---

## 5. Storage pipeline

### Primary: Backblaze B2

Bucket:

`Education-Dept-Files`

Canonical S3 endpoint:

`https://s3.us-east-005.backblazeb2.com`

Object naming convention:

```text
telegram-intake/YYYY-MM-DD/<telegram_intake_id>/<safe_filename>
```

### Backup: Google Drive

The backup folder is configured through the GitHub secret:

`GOOGLE_DRIVE_BACKUP_FOLDER_ID`

The worker is retry-safe. Existing B2 and Drive objects are reused where possible.

### Integrity

Each stored file receives a SHA-256 checksum. Storage metadata records the checksum, size, B2 key, Drive file ID, storage status and verification state.

Expected successful state:

```text
telegram_intake.status = Stored
storage.b2_status      = AVAILABLE
storage.drive_status   = AVAILABLE
storage.verified       = true
```

Implementation: [`storage_worker.py`](./../storage/storage_worker.py)  
Workflow: [`global-storage-worker.yml`](../../../.github/workflows/global-storage-worker.yml)

---

## 6. Document processing

The document processor consumes verified stored Telegram files.

Candidate intake states:

- `Stored`
- `Processing Failed` (retry/recovery path)

Processing sequence:

1. Locate verified B2 object.
2. Download the file.
3. Try embedded PDF text extraction.
4. If embedded text is insufficient, render PDF pages.
5. Run Hindi + English Tesseract OCR.
6. Clean and normalize extracted text.
7. Extract structured metadata.
8. Insert the durable record into Supabase `documents`.
9. Mark the intake record as processed.

Implementation: [`document_processor.py`](./document_processor.py)  
Workflow: [`global-document-processor.yml`](../../../.github/workflows/global-document-processor.yml)

### Extracted metadata

Typical fields include:

- subject
- issuing authority
- reference number
- printed issue date
- normalized issue date
- short description
- detailed summary
- category/category key
- extraction method
- extraction confidence
- full OCR text
- checksum and storage references
- publication state

### Subject rule

The public table must contain the **actual short subject**, not the full OCR body. Generic fallbacks such as `Official Letter`, `Document`, or `Letter` should not be used when a meaningful subject can be extracted.

### Special recognition

The processor includes explicit recognition for Bihar education/BSEB material, including Spot Admission terminology and the Bihar School Examination Board authority.

---

## 7. Publication pipeline

The publication worker selects completed, safe documents.

A normal document is eligible when it is:

- `processing_status = Completed`
- `publication_status = Unpublished`
- backed by a Drive file
- not sensitive
- not duplicate
- useful
- extraction confidence is HIGH or MEDIUM
- has a subject

A reliably machine-readable issue date is useful metadata but is **not a mandatory publication gate**.

Publication performs these actions:

1. Obtain a Google OAuth access token from the configured refresh token.
2. Give the Drive file public reader access.
3. Store a public Drive download URL.
4. Set `approved_for_publication = true`.
5. Set `publication_status = Published`.
6. Record publication time/reason and increment the public revision.

Implementation: [`publication_worker.py`](./publication_worker.py)  
Workflow: [`global-document-publication.yml`](../../../.github/workflows/global-document-publication.yml)

---

## 8. Public archive contract

The public archive is Hindi-first and displays:

| Column | Meaning |
|---|---|
| Sr.No. | Serial number in current result order |
| Letter Type | Derived document type |
| Issuing Authority | Source office/authority |
| Issued Date | Original document date |
| Upload Date | Pipeline receipt/publication timing |
| Subject | Short actual subject |
| Download | Public file action |

The archive uses the Supabase view:

`approved_public_documents`

The view exposes the public branch only when the document satisfies publication conditions. Failed Telegram documents can be surfaced through their secure review path.

Archive implementation in the school repository:

- [`school-document-archive.html`](https://github.com/zzpsah/umv-tetahali-staging/blob/main/school-document-archive.html)
- [`document-archive.js`](https://github.com/zzpsah/umv-tetahali-staging/blob/main/assets/document-archive.js)
- [`document-archive-config.js`](https://github.com/zzpsah/umv-tetahali-staging/blob/main/assets/document-archive-config.js)

---

## 9. Supabase data model

### `telegram_intake`

Intake/control record for Telegram-originated items. It tracks the original message/file, processing status and storage metadata.

Typical lifecycle:

```text
Received
   |
   v
Stored
   |
   v
Processed
```

Failure/retry states include:

```text
Storage Failed
Storage Partial
Processing Failed
```

### `documents`

Durable document metadata and processing record. This is the document system's structured index, not the file store.

### `processing_jobs`

Queue/job tracking for processing operations.

### `approved_public_documents`

Public-facing database view for safe archive listing.

---

## 10. Status model

### Processing

```text
New -> Queued -> Processing -> Completed
                         \-> Processing Failed
                         \-> Needs Manual Review
```

Other supported lifecycle values include `Action Required`, `Reviewed`, `Approved`, `Duplicate`, `Ignored` and `Archived` where applicable.

### Publication

```text
Unpublished -> Published
             \-> Unpublished by Admin
             \-> Unavailable
             \-> Superseded
```

### Priority

`URGENT`, `HIGH`, `NORMAL`, `LOW`, `IGNORE`

### Forwarding

`Not Forwarded`, `Ready to Forward`, `Forwarded`, `Do Not Forward`

---

## 11. Failure and manual review policy

`04_Manual_Review` is **not a normal approval queue**.

Use manual review when:

- storage cannot be completed
- OCR/extraction genuinely fails
- metadata cannot be recovered safely
- publication fails and requires intervention
- a duplicate/sensitive/problematic document needs a human decision

Even a failed document should remain visible to the operational system with its failure state and secure review path. Records are not physically deleted just because processing failed.

---

## 12. GitHub Actions

Production workflows:

- [`global-storage-worker.yml`](../../../.github/workflows/global-storage-worker.yml) — Telegram → B2 → Drive
- [`global-document-processor.yml`](../../../.github/workflows/global-document-processor.yml) — B2 → OCR → Supabase
- [`global-document-publication.yml`](../../../.github/workflows/global-document-publication.yml) — Supabase → public Drive → archive
- [`global-system-health.yml`](../../../.github/workflows/global-system-health.yml) — global health checks

Most production workers support both scheduled execution and manual `workflow_dispatch`. Storage also has a push trigger so a repository change can initiate a run; the scheduled trigger remains as a safety net.

Actions dashboard:

https://github.com/zzpsah/automation-suite/actions

---

## 13. Required GitHub secrets

Never put secret values in source code or README files.

Storage/processing/publication require configured repository secrets including:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
TELEGRAM_BOT_TOKEN
B2_KEY_ID
B2_APPLICATION_KEY
B2_BUCKET_NAME
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN
GOOGLE_DRIVE_BACKUP_FOLDER_ID
```

The service-role key, bot token, B2 application key and Google refresh token are confidential.

---

## 14. Current tested end-to-end result

The test document **Spot admission extension letter.pdf** completed the complete storage and processing path.

Verified outcomes included:

- Telegram intake recorded
- B2 primary storage available
- Google Drive backup available
- SHA-256 verification successful
- document processing completed
- BSEB authority extracted
- Spot Admission subject recognized
- publication completed
- public Drive URL created
- `approved_public_documents` can expose the published record

This establishes the working baseline for continuing production hardening.

---

## 15. Operational rules

1. **Do not disable the existing Apps Script pipeline.**
2. **Do not add R2 or a third file-storage system.**
3. **Supabase remains the metadata/control plane.**
4. **B2 is primary; Google Drive is backup.**
5. **Telegram is input/transport, not storage.**
6. **Successful documents do not require human approval.**
7. **Manual review is reserved for genuine failures or exceptional cases.**
8. **Never publish sensitive or duplicate records.**
9. **Do not expose service-role keys, bot tokens, OAuth refresh tokens or B2 application keys.**
10. **Keep production OCR integration separate from the independently maintained Global Sarkari OCR project.**
11. **Preserve source provenance and audit information.**
12. **Prefer safe, explainable metadata extraction over invented metadata.**

---

## 16. Related documentation

- [Global Automation Toolkit](../../README.md)
- [Global Sarkari OCR](../../ocr/README.md) — separate reusable OCR project
- [Automation Suite root](../../../README.md)
- [School staging repository](https://github.com/zzpsah/umv-tetahali-staging)
- [School public repository](https://github.com/zzpsah/umv-tetahali)
