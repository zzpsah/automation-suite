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
- Local session persistence and recovery
- Android Save As PDF and PDF sharing
- EXIF-aware captured image orientation

## Architecture
`CameraX → Capture → DocumentDetector → PerspectiveNormalizer → Filter → ScanPage → PDF/OCR adapters`

The app is intentionally local-first in Phase 1. The original captured image is retained during processing, and OCR is a provider boundary rather than a fake implementation.

## Quality / Beta Gate

A successful Gradle build is **not** sufficient for release. The permanent validation pipeline requires:

1. Debug and release compilation
2. Unit tests
3. APK signing/integrity verification
4. Android emulator installation with `adb`
5. App launch and process verification
6. Automated functional beta testing
7. Critical scanner journey verification before an APK is shared

The planned automated beta layers are Firebase Test Lab/Robo Test for device-matrix exploration and Maestro for deterministic end-to-end UI journeys. See [`docs/BETA_TESTING.md`](docs/BETA_TESTING.md) for the permanent release gate and future test coverage.

**Rule: BUILD PASS ≠ APP PASS.** A candidate that cannot install, launch, or complete a mandatory functional workflow must not be distributed as a final/beta APK.
