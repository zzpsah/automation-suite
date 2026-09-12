# DevOS Premium Document Scanner — Phase 1

Kotlin + Jetpack Compose + CameraX + OpenCV Android document scanner.

## Phase 1 working scope
- CameraX high-quality capture
- Automatic post-capture document quadrilateral detection
- Perspective correction
- Manual four-corner adjustment
- Original / Auto / Mono / B&W enhancement filters
- Batch page collection in one scan session
- PDF export using Android PdfDocument
- OCR-ready `OcrEngine` boundary (provider-independent)
- Premium dark Compose UI

## Architecture
`CameraX → Capture → DocumentDetector → PerspectiveNormalizer → Filter → ScanPage → PDF/OCR adapters`

The app is intentionally local-first in Phase 1. The original captured image is retained during processing, and OCR is a provider boundary rather than a fake implementation.
