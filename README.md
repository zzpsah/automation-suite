# Automation Suite

A single repository for the school's reusable automation systems and production workflows.

## Projects

| Project | Purpose | Documentation |
|---|---|---|
| `global-automation/` | Shared GitHub Actions, storage, document processing and system automation | [Global Automation README](global-automation/README.md) |
| `global-automation/scripts/document/` | **School Document Pipeline**: storage → OCR/text extraction → metadata → publication | [School Document Pipeline README](global-automation/scripts/document/README.md) |
| `global-automation/scripts/storage/` | Telegram → Backblaze B2 → Google Drive storage layer | [Storage README](global-automation/scripts/storage/README.md) |
| `global-automation/govdoc-ocr/` | **GovDOC OCR Engine**: reusable OCR, normalization and government-document metadata extraction | [GovDOC OCR README](global-automation/govdoc-ocr/README.md) |
| `phone-printer/` | Android phone → hotspot → Windows PC → USB printer bridge | — |
| `paint-gemini-app/` | PyQt6 image editor with drawing tools and AI assistance | — |
| `browser-portal-automation/` | Browser-based portal collection, attachment processing, OCR, classification and archiving | — |

## School Document Pipeline

The production document system for **UCHCH MADHYAMIK VIDALAY, TETAHALI**, UDISE `10160203806`, BSEB College Code `42369`.

### System flow

```text
Telegram / existing Drive intake
            |
            v
     Supabase control plane
            |
            v
      Backblaze B2 PRIMARY
            |
            v
      Google Drive BACKUP
            |
            v
       SHA-256 verify
            |
            v
   Global Document Processor
            |
            v
       GovDOC OCR Engine
            |
            v
      Supabase documents
            |
            v
     Publication Worker
            |
            v
    Public Document Archive
```

### Production links

- [School staging site](https://zzpsah.github.io/umv-tetahali-staging/index.html)
- [Public Document Archive](https://zzpsah.github.io/umv-tetahali-staging/school-document-archive.html)
- [Official Documents](https://zzpsah.github.io/umv-tetahali-staging/official-documents.html)
- [Official Updates](https://zzpsah.github.io/umv-tetahali-staging/official-updates.html)
- [Notices](https://zzpsah.github.io/umv-tetahali-staging/notices.html)
- [Private Document Manager](https://zzpsah.github.io/umv-tetahali-staging/private-documents.html)
- [Secure Review](https://zzpsah.github.io/umv-tetahali-staging/document-review.html)
- [School staging repository](https://github.com/zzpsah/umv-tetahali-staging)
- [School main repository](https://github.com/zzpsah/umv-tetahali)
- [GitHub Actions](https://github.com/zzpsah/automation-suite/actions)

## Production workflows

- [`global-storage-worker.yml`](.github/workflows/global-storage-worker.yml)
- [`global-document-processor.yml`](.github/workflows/global-document-processor.yml)
- [`global-document-publication.yml`](.github/workflows/global-document-publication.yml)
- [`global-system-health.yml`](.github/workflows/global-system-health.yml)

## Important architecture rules

- **Backblaze B2 is the primary file store.**
- **Google Drive is the backup and public delivery source.**
- **Supabase is the durable metadata/control plane, not the file store.**
- **Telegram is input/transport, not long-term storage.**
- **The existing Apps Script pipeline remains active and untouched.**
- `04_Manual_Review` is for genuine failures/exceptions, not normal approval.
- Successful documents publish automatically when they meet publication safety rules.
- Sensitive and duplicate documents are not automatically published.
- Secrets are stored only in GitHub/Supabase configuration, never in source.

## Documentation policy

Each production subsystem should have a local README explaining:

1. purpose
2. architecture
3. inputs/outputs
4. data lifecycle
5. configuration and required secrets
6. failure/retry behavior
7. workflows
8. security rules
9. links to related school resources

The **GovDOC OCR Engine** is intentionally maintained separately from the School Document Pipeline. The school pipeline may consume it as a reusable OCR dependency, but OCR engine/model/language-pack improvement must not destabilize production document processing.
