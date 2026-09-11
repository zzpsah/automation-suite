# Global Sarkari OCR

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The school document pipeline is only one consumer. Future OCR-related projects should reuse this engine instead of copying or forking OCR logic.

## Independence contract

The OCR package must not require:

- Telegram
- Supabase
- Backblaze B2
- Google Drive
- GitHub Actions
- any school, district, portal, or department database

Those systems can call the OCR package, but the OCR package must work locally/offline once its runtime dependencies are installed.

## Stable entry point

Use `ocr_service.process_pdf(pdf_path, work_dir)` when a project needs PDF text + government-document metadata. It returns OCR text, extraction method, metadata, category and confidence without requiring network credentials.

Project-specific business logic belongs in the consuming project, not in this package.

## Current engine

- Embedded PDF text extraction when sufficient
- Tesseract Hindi + English OCR fallback
- Sarkari text normalization
- Hindi/English administrative label recognition
- Bihar Education terminology pack
- Conservative metadata extraction
- Regression corpus and CI tests

## Processing model

```text
PDF / Image
    ↓
Core OCR engine
    ├── embedded text
    └── Tesseract hin+eng
    ↓
Sarkari normalizer
    ↓
Metadata extraction
    ↓
Category + confidence
    ↓
Consumer project
```

## Language/domain roadmap

1. Bihar Education
2. Bihar Government
3. Other State Governments
4. Central Government
5. Shared cross-government terminology

Language/domain knowledge that is reusable across projects should go into `language_packs/`. Project-specific rules must remain outside the package.

## Training / improvement model

This is a **corpus-driven improvement system**, not a claim that the repository has trained a new OCR model. The process is:

`real document → OCR sample → confirmed error → reusable correction → regression test → CI → benchmark`

Every confirmed correction should become a test case. Never change a test merely to hide a regression.

## OCR backend roadmap

Tesseract is the current free baseline. Future backends such as PaddleOCR, OCR-VL or other local/open models can be added behind the same interface. A new backend should be benchmarked against the existing corpus before becoming the default.

## Language policy

The normalizer is not a translator. It should:

1. preserve source OCR text;
2. identify Hindi/English administrative labels;
3. normalize safe spelling/spacing variants;
4. prefer document wording for subject and authority;
5. use controlled terminology only when supported by source text;
6. never invent dates, reference numbers, authorities or actions.

## Security and deployment

- Never commit API tokens, service-role keys, refresh tokens or storage credentials.
- Tesseract binaries are runtime dependencies, not repository assets.
- OCR must not make publication/approval decisions.
- Missing or low-confidence metadata remains missing/low-confidence.

## Documentation for future upgrades

- `DESIGN.md` — architecture, compatibility, corpus strategy and upgrade checklist
- `CHANGELOG.md` — version/compatibility history
- `language_packs/` — reusable government-domain terminology
- `tests/` — regression corpus and executable expectations

## Relationship to existing systems

The existing school `document_processor.py` remains a consumer during migration. The reusable OCR layer is intentionally kept separate so that student-registration documents, portal automation, scanned applications, government letters, notices, orders, certificates and future projects can all reuse the same OCR foundation.
