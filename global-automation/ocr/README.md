# Global Sarkari OCR

Standalone, reusable OCR and document-text processing component for government/school documents.

## Canonical development location

**Repository:** `zzpsah/automation-suite`

**Development branch:** `feature/global-sarkari-ocr`

**Branch:** https://github.com/zzpsah/automation-suite/tree/feature/global-sarkari-ocr

**OCR folder:** `global-automation/ocr/`

**OCR folder on development branch:** https://github.com/zzpsah/automation-suite/tree/feature/global-sarkari-ocr/global-automation/ocr

## Important

The `main` branch contains the stable/shared location for the OCR project. Active OCR development and improvement currently continues on `feature/global-sarkari-ocr` until that branch is intentionally merged/promoted.

School Document Pipeline and other production projects should reference this project as a separate reusable component. Do not mix OCR experimentation/training with production pipeline logic.

## Project contents

The OCR project includes the reusable OCR engine, preprocessing, correction, normalization, subject extraction, taxonomy, Bihar language packs, tests, benchmarks, diagnostics and the separate continuous-improvement/training area.

## Related project

School Document Pipeline: `global-automation/scripts/document/`

Production document processing must remain independently deployable even when OCR is being improved.

## Recovery rule

If the OCR folder is not visible in a UI, first open the repository `zzpsah/automation-suite`, then open `global-automation`, then `ocr`. If a specific working version is required, switch to `feature/global-sarkari-ocr` before inspecting or modifying OCR code.
