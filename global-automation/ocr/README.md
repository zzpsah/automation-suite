# Global Sarkari OCR

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The school document pipeline is only one consumer. Future OCR-related projects should reuse this engine instead of copying or forking OCR logic.

## Independence contract

The OCR package must not require Telegram, Supabase, Backblaze B2, Google Drive, GitHub Actions, or any school/district/portal database. It should work locally/offline once runtime dependencies are installed.

## Stable entry point

Use `ocr_service.process_pdf(pdf_path, work_dir)` or `ocr_service.process_file(file_path, work_dir)`. Consumers should not import internal engine/backend modules directly.

## Core runtime pipeline

```text
PDF
 ↓
OCR service
 ↓
Backend selection
 ↓
Preprocessing profile
 ↓
OCR engine (embedded text → Tesseract fallback)
 ↓
Correction
 ↓
Sarkari normalizer + subject extraction
 ↓
District/office resolver + taxonomy
 ↓
Page diagnostics
 ↓
Quality confidence
 ↓
Consumer project
```

## Separate improvement pipeline

Training/improvement is intentionally a separate process:

```text
Reviewed OCR pairs
      ↓
Corpus collector
      ↓
Candidate miner
      ↓
Evaluation / regression tests
      ↓
Training artifacts + report
      ↓
Human/code review
      ↓
Approved correction or model/backend update
      ↓
Benchmark
      ↓
Release
```

The scheduled workflow `.github/workflows/global-ocr-training.yml` builds reviewable artifacts. It **does not directly modify** `correction.py`, language packs, the default backend, or production consumers. This prevents self-training from silently degrading OCR quality.

### What can be learned automatically

- repeated OCR token errors
- safe spelling/label variants
- authority and office aliases
- document-type vocabulary
- subject extraction patterns
- preprocessing/backend performance signals

### What should require review before becoming runtime behavior

- new automatic substitutions
- changes to official names
- new taxonomy categories
- changes to confidence thresholds
- default backend changes
- model weights or fine-tuning datasets

A future true OCR-model fine-tuning job can consume the same reviewed corpus, but model training remains a separate backend-specific concern. The core service contract stays unchanged.

## Backend architecture

`backend.py` defines the shared backend contract. Tesseract is the current implementation. Future local/open backends can implement the same `OCRBackend` interface and be registered only after passing tests and benchmarks. The consumer contract does not change when the backend changes.

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

This is a **corpus-driven improvement system**, not a claim that the repository has trained a new OCR model. Every confirmed correction becomes a regression case.

`real document → OCR sample → confirmed error → corpus → candidate → review → regression test → benchmark → release`

Never change a test merely to hide a regression.

## Language policy

The normalizer is not a translator. Preserve source wording, normalize only safe variants, use controlled terminology only when supported by source text, and never invent dates, reference numbers, authorities or actions.

## Security

Never commit API tokens, service-role keys, refresh tokens or storage credentials. OCR must not make publication/approval decisions. Preserve original OCR evidence in consuming systems; corrected text is a derived representation.

## Future upgrades

- Add real Bihar Education OCR samples with provenance.
- Add more Bihar authority aliases through language packs.
- Add district/block vocabulary through scoped language packs.
- Add benchmark accuracy labels, not only runtime measurements.
- Add advanced deskew/rotation only after benchmark evidence.
- Add backend-specific model-training adapters.
- Add structured error diagnostics without exposing document content.
- Publish a migration note before changing the default backend.
