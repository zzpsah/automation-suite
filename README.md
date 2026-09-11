# Automation Suite

A single repository for the school's reusable automation systems and production workflows.

> **DevOS recovery rule:** this repository is the engineering source of truth. Every material architecture decision, implemented capability, release constraint, recovery path, and next-step plan must be recorded in the relevant README/docs as part of the same development work. A new DevOS session should be able to recover the project from GitHub without depending on chat history.

## Projects

| Project | Purpose | Documentation |
|---|---|---|
| `global-automation/` | Shared GitHub Actions, storage, document processing and system automation | [Global Automation README](global-automation/README.md) |
| `global-automation/scripts/document/` | **School Document Pipeline**: storage → OCR/text extraction → metadata → publication | [School Document Pipeline README](global-automation/scripts/document/README.md) |
| `global-automation/scripts/storage/` | Telegram → Backblaze B2 → Google Drive storage layer | [Storage README](global-automation/scripts/storage/README.md) |
| `global-automation/ocr/` | **Government Document Vision & OCR Platform**: reusable OCR, vision, layout and government-document intelligence | [OCR README](global-automation/ocr/README.md) |
| `phone-printer/` | Android phone → hotspot → Windows PC → USB printer bridge | — |
| `paint-gemini-app/` | PyQt6 image editor with drawing tools and AI assistance | — |
| `browser-portal-automation/` | Browser-based portal collection, attachment processing, OCR, classification and archiving | — |

## DevOS engineering continuity

This repository is the engineering source of truth so DevOS can recover work after a chat/session change.

### Source-of-truth hierarchy

```text
GitHub repository
   ↓
Relevant project README / DESIGN / architecture docs
   ↓
Code + tests
   ↓
PR / commit history
   ↓
Chat conversation
```

Chat is context, **not the authoritative implementation record**.

### Development protocol

For every material development step:

1. Inspect the current branch/source before changing architecture.
2. Implement the smallest coherent production-grade increment.
3. Add or update regression tests where applicable.
4. Update the relevant README/documentation in the same development sequence.
5. Record architectural constraints and known limitations.
6. Record the next logical development step when useful for recovery.
7. Commit changes with descriptive messages.
8. Never claim tests/CI passed unless an actual execution or verified CI result exists.
9. Preserve backward-compatible consumer APIs unless a deliberate versioned change is documented.
10. Never put secrets, credentials, or private source evidence into documentation.

### Recovery checklist

```text
1. Identify repository + branch
2. Read root README
3. Read relevant project README
4. Inspect latest commits / PR state
5. Inspect current code, tests and documented limitations
6. Continue from the documented roadmap
7. Update documentation with the implementation
```

### Documentation rule

**If DevOS learns it during development and it matters for future engineering, it belongs in GitHub.** This includes architecture decisions, APIs, data flow, benchmarks, model/artifact policy, security boundaries, limitations, migration notes, release gates, recovery instructions, and roadmap state.

## Government Document Vision & OCR Platform — current recovery point

The canonical development branch is `feature/global-ocr-platform` and PR #6 remains the single canonical PR. The OCR platform now has P19 cross-document relations, P20 conservative candidate clustering, a reusable deterministic global search index, and P21 evidence-only reference/date timeline intelligence. Search remains separate from clustering, and all derived layers preserve document/page/block/entity provenance.

P20 deliberately does not claim same legal-case identity. P21 does not assign legal meaning to dates; it only orders explicitly extracted date entities and attaches same-block reference evidence. Current development is **not production-certified** until the full OCR suite and CI are actually verified.

**Next OCR recovery step:** verify the full regression suite/CI, then add persistent search adapters and metadata filters before semantic/vector retrieval.

## School Document Pipeline

The production document system for **UCHCH MADHYAMIK VIDALAYA, TETAHALI**, UDISE `10160203806`, BSEB College Code `42369`.

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
      Supabase documents
            |
            v
     Publication Worker
            |
            v
    Public Document Archive
```

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

## Production links

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

## Documentation policy

Each production subsystem should have a local README explaining purpose, architecture, inputs/outputs, lifecycle, configuration, failure/retry behavior, workflows, security, current status, known limitations, and recovery/next-step notes.

The **Government Document Vision & OCR Platform** is intentionally maintained separately from the School Document Pipeline. The school pipeline may consume it as a reusable dependency, but OCR model/language-pack improvement must not destabilize production document processing.
