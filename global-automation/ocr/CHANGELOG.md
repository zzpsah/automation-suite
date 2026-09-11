# Global Sarkari OCR Changelog

## 1.1.0 — Image Processing Foundation

### Added
- Advanced reusable image preprocessing package.
- EXIF orientation normalization.
- Deterministic image resizing for oversized phone/scanner images.
- Conservative skew estimation and deskew for small rotations.
- Contrast normalization, denoising, sharpening and a threshold candidate.
- Automatic OCR candidate selection using a privacy-safe text quality heuristic.
- Image quality diagnostics including dimensions, luminance, contrast, dark-pixel ratio and skew estimate.
- Stable `process_image()` API and image support through `process_file()`.
- Regression tests for image analysis, variant generation and stable service behavior.

### Design guarantees
- Source images are never overwritten.
- Preprocessing is independent of Tesseract/PaddleOCR/VLM implementation.
- Candidate selection is a runtime heuristic, not a benchmark accuracy claim.
- Ground-truth benchmarks remain the promotion gate for future models/backends.
- No external service, database, storage provider or project-specific workflow is required.

## 1.0.0 — Global OCR Platform Foundation

### Added
- Reusable Hindi/English Sarkari OCR engine.
- Conservative Sarkari text normalizer.
- Bihar Education language pack.
- Bihar Education metadata regression corpus.
- Controlled artifact manifests and SHA-256 verification.
- Tesseract, PaddleOCR and future VLM backend boundaries.
- Separate Global Document Processing Engine.
- CI validation for OCR runtime and metadata extraction.
