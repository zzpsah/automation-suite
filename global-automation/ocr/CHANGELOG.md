# Government Document Vision & OCR Platform (GovDoc Vision) Changelog

## Unreleased — feature/global-sarkari-ocr

### Naming
- Canonical product name is **Government Document Vision & OCR Platform**.
- Short name is **GovDoc Vision**.
- **Global OCR** is retained only as engineering shorthand/legacy continuity.
- Package path remains `global-automation/ocr/` to avoid unnecessary code-path churn.

### Added
- Reusable Hindi/English Sarkari OCR engine.
- Conservative Sarkari text normalizer.
- Bihar Education language pack.
- Bihar Education metadata regression corpus.
- CI validation for Tesseract Hindi/English runtime and metadata extraction.
- Document Processor v2 integration using the reusable OCR package.
- Non-file intake filtering so text records are not sent through PDF OCR.
- Government Document Intelligence baseline.
- Capability matrix and deterministic self-test.
- Design and future-upgrade documentation.

### Compatibility
- Existing Telegram intake, B2 primary storage, Google Drive backup, Supabase metadata, and publication workflows remain separate from the GovDoc Vision package.
- Existing Apps Script document pipeline is not modified by this branch.

### Planned
- Expand Bihar authority aliases and document taxonomy.
- Add OCR correction rules from real-world scanned government documents.
- Add date/reference/subject quality scoring.
- Add pluggable OCR backends and benchmark them against the same corpus.
- Add layout/bounding-box evaluation and advanced image processing after representative tests.
