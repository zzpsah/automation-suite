# DEVOS Premium Document Scanner — Architecture

## 1. Purpose

DEVOS Scan is a local-first Android document scanner designed for photographed paperwork, including forms containing printed text, handwriting, checkboxes, photos and signatures.

Phase 1 uses Kotlin, Jetpack Compose, CameraX and OpenCV. The architecture deliberately separates capture, document geometry, image enhancement, page/session state, export and OCR so later upgrades do not require rewriting the UI.

## 2. Pipeline

```text
CameraX Preview
    ↓
ImageCapture (MAXIMIZE_QUALITY)
    ↓
Captured JPEG / Bitmap
    ↓
DocumentDetector (OpenCV)
    ↓
PerspectiveNormalizer
    ↓
Image Enhancement Filter
    ↓
ScanPage / Batch Session
    ├── Review
    ├── Manual adjustment
    └── PDF export
    ↓
OCR adapter boundary (future provider)
```

## 3. Components

### MainActivity
Owns the Phase 1 Compose application flow:
- camera permission
- camera screen
- capture callback
- review/batch screen
- fine-tune screen
- PDF export action

### ImageProcessor
OpenCV-based image processing:
- RGBA → grayscale conversion
- Gaussian blur
- Canny edge detection
- contour discovery
- polygon approximation
- four-corner document candidate selection
- corner ordering
- perspective warp
- enhancement filters

The current automatic detector is **post-capture**, not a live edge detector or automatic shutter model.

### ScannerModels
Defines stable domain boundaries:
- `Quad`: four document corners
- `ScanFilter`: Original, Auto, Mono, B&W
- `ScanPage`: processed page plus geometry/filter metadata
- `OcrEngine`: provider-independent OCR contract

### PdfExporter
Converts the current batch of pages to a PDF using Android `PdfDocument`.

### CI
GitHub Actions builds debug/release APKs and runs unit tests. The CI workflow is the authoritative build verification path when a local Android SDK is unavailable.

## 4. Geometry model

Corners are ordered:
1. top-left
2. top-right
3. bottom-right
4. bottom-left

The detector evaluates large contours, approximates them with `approxPolyDP`, and accepts a four-point candidate when its area exceeds the configured 12% image-area threshold.

Perspective output dimensions are derived from the maximum opposite-edge widths/heights, then `getPerspectiveTransform` and `warpPerspective` produce a normalized page.

## 5. Enhancement model

- **Original**: preserve captured pixels.
- **Auto**: grayscale + CLAHE for local contrast improvement.
- **Mono**: grayscale.
- **B&W**: Gaussian blur + adaptive Gaussian threshold.

Enhancement is intentionally deterministic and local in Phase 1. There is no network dependency and no fabricated OCR result.

## 6. OCR boundary

`OcrEngine` is an interface only. A future implementation may use an on-device or remote provider. OCR must receive the actual processed bitmap and return extracted text; the scanner must never claim OCR success without a provider result.

For government/school forms, downstream field extraction should remain conservative and editable before any authoritative database matching.

## 7. Known architectural gaps for Phase 2

- Retain original capture alongside processed page for true re-cropping after manual corner adjustment.
- Map editor coordinates precisely between displayed image coordinates and source bitmap coordinates.
- Apply flash state to `ImageCapture` rather than only changing the UI icon.
- Add live document-edge detection/overlay and optional auto-shutter.
- Add persistent scan sessions with Room/DataStore.
- Add Android Storage Access Framework Save As/share flow.
- Add gallery/import support.
- Add real OCR provider adapters and structured field extraction.
- Add device/emulator integration tests and representative photographed-form fixtures.
- Add memory/large-image safeguards for long batch sessions.
