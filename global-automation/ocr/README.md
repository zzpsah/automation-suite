# Global Sarkari OCR

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The school document pipeline is only one consumer. Future OCR-related projects should reuse this engine instead of copying or forking OCR logic.

## Independence contract

The OCR package must not require Telegram, Supabase, Backblaze B2, Google Drive, GitHub Actions, or any school/district/portal database. It should work locally/offline once runtime dependencies are installed.

## Stable entry point

Use `ocr_service.process_pdf(pdf_path, work_dir)` or `ocr_service.process_file(file_path, work_dir)`. Consumers should not import internal engine/backend modules directly.

## Current pipeline

```text
PDF
 ↓
OCR service
 ↓
OCR engine (embedded text → Tesseract fallback)
 ↓
Correction
 ↓
Sarkari normalizer + multiline subject
 ↓
Quality-based confidence
 ↓
Consumer project
```

## Backend architecture

`backend.py` defines the shared backend contract. Tesseract is the current implementation. Future local/open backends can implement the same `OCRBackend` interface and be registered only after passing tests and benchmarks. The consumer contract does not change when the backend changes.

`benchmark.py` provides a lightweight timing/output-size harness for rendered images. It deliberately does not log document text. Backend comparison should use the same labelled corpus and include accuracy/extraction quality in addition to runtime.

## Page diagnostics

`diagnostics.py` provides privacy-safe measurements for each OCR page: output character count, non-whitespace character count, non-empty line count, blank-page detection, and a conservative `likely_weak` flag. Diagnostics never return or log page text. They can be used by consumers to decide whether a page should be retried with another preprocessing profile or backend.

## Language/domain roadmap

1. Bihar Education
2. Bihar Government
3. Other State Governments
4. Central Government
5. Shared cross-government terminology

Reusable terminology belongs in `language_packs/`; project-specific business rules stay outside this package.

## Training / improvement model

This is a **corpus-driven improvement system**, not a claim that the repository has trained a new OCR model:

`real document → OCR sample → confirmed error → reusable correction → regression test → CI → benchmark`

Every confirmed correction becomes a regression case. Never change a test merely to hide a regression.

## Language policy

The normalizer is not a translator. Preserve source wording, normalize only safe variants, use controlled terminology only when supported by source text, and never invent dates, reference numbers, authorities or actions.

## Security

Never commit API tokens, service-role keys, refresh tokens or storage credentials. OCR must not make publication/approval decisions. Preserve original OCR evidence in consuming systems; corrected text is a derived representation.

## Future upgrades

- Add real Bihar Education OCR samples with provenance.
- Add more Bihar authority aliases through language packs.
- Add document-type taxonomy versioning.
- Benchmark every backend against the same corpus.
- Add advanced deskew/rotation only after benchmark evidence.
- Add structured error diagnostics without exposing document content.
- Publish a migration note before changing the default backend.
