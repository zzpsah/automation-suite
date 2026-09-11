# Global Sarkari OCR Changelog

## Unreleased — feature/global-sarkari-ocr

### Added
- Reusable Hindi/English Sarkari OCR engine.
- Conservative Sarkari text normalizer.
- Bihar Education language pack.
- Bihar Education metadata regression corpus.
- CI validation for Tesseract Hindi/English runtime and metadata extraction.
- Document Processor v2 integration using the reusable OCR package.
- Non-file intake filtering so text records are not sent through PDF OCR.
- Design and future-upgrade documentation.

### Compatibility
- Existing Telegram intake, B2 primary storage, Google Drive backup, Supabase metadata, and publication workflows remain separate from the OCR package.
- Existing Apps Script document pipeline is not modified by this branch.

### Planned
- Expand Bihar authority aliases and document taxonomy.
- Add OCR correction rules from real-world scanned government documents.
- Add date/reference/subject quality scoring.
- Add pluggable OCR backends and benchmark them against the same corpus.
