# Global Sarkari OCR

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The school document pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## Stable consumer API

```python
from ocr import process_file, process_pdf, process_image

result = process_file("document.pdf", "/tmp/ocr-work")
result = process_file("scan.jpg", "/tmp/ocr-work")
```

Consumers receive source-preserving full text, ordered page text, diagnostics, metadata, taxonomy and confidence. Backend internals remain private.

## Core runtime pipeline

```text
PDF / Image
 ↓
Input validation
 ↓
Image quality analysis
 ↓
EXIF orientation + resize + deskew
 ↓
Denoise + contrast + sharpen + threshold candidates
 ↓
OCR backend
 ↓
Candidate quality selection
 ↓
Correction
 ↓
Sarkari normalizer + subject extraction
 ↓
District/office resolver + taxonomy
 ↓
Page diagnostics + confidence
 ↓
Consumer project
```

The image layer is deliberately backend-neutral. Tesseract currently performs candidate inference; PaddleOCR and future VLM implementations use the same backend contract.

## Image processing capabilities

- EXIF orientation normalization for phone photos.
- Conservative small-angle deskew; large rotations are not blindly guessed.
- Deterministic resize/upscale to a useful OCR resolution while preventing oversized images.
- Grayscale normalization and autocontrast.
- Median denoising for scanner/phone noise.
- Mild sharpening and contrast enhancement.
- Optional hard-threshold candidate for faded monochrome scans.
- Multiple-candidate OCR and deterministic selection.
- Privacy-safe image quality measurements: dimensions, luminance, contrast, dark-pixel ratio and estimated skew.
- Original images are never overwritten.

Candidate selection is a runtime heuristic, **not** an accuracy claim. Ground-truth CER/WER and field accuracy remain release gates.

## Page preservation

PDF processing keeps ordered page text and privacy-safe page diagnostics. Consumers can identify blank/weak pages and retry or route them to another backend without losing the original evidence.

## Separate improvement pipeline

```text
Production projects
      ↓ feedback / corrections / errors
Global OCR Training
      ├── OCR error mining
      ├── Hindi improvement
      ├── Sarkari terminology
      ├── Bihar vocabulary
      ├── aliases
      ├── regression corpus
      └── benchmark
      ↓
Validated release
      ↓
ALL PROJECTS
```

Training never runs inside School Document Pipeline and never silently edits production runtime behavior. Model training is backend-specific; the consumer API remains stable.

## Backend architecture

```text
Global OCR Engine
 ├── Tesseract
 ├── PaddleOCR
 └── Future VLM
```

Backends are interchangeable implementations, not training systems. A backend is enabled only after contract tests, benchmark validation and explicit version/artifact registration.

## Controlled artifacts

Large models and binaries are not committed to Git. Production accepts only explicit artifact versions recorded in `artifacts/manifest.json` and verified by SHA-256. `latest` is rejected by policy and checksum mismatches fail closed.

## Training / improvement

`real document → OCR sample → confirmed error → corpus → candidate → review → regression test → benchmark → release`

The training workflow produces reviewable candidates. It does not automatically change correction rules, language packs, confidence thresholds, backend selection or model weights.

## Language policy

The normalizer is not a translator. Preserve source wording, normalize only safe variants, use controlled terminology only when supported by source text, and never invent dates, reference numbers, authorities or actions.

## Security and separation

- No Telegram, Supabase, B2, Google Drive or school database dependency.
- No secrets or credentials in OCR source/artifacts.
- Original OCR evidence remains available to consumers.
- Derived metadata never becomes an approval/publication decision.
- School Document Pipeline remains a consumer, not an OCR training owner.

## Roadmap

1. Add real reviewed Bihar Education image/PDF corpus with provenance.
2. Add CER/WER and field-level golden benchmarks.
3. Add backend-specific confidence calibration.
4. Add PaddleOCR production artifact once pinned and benchmarked.
5. Add a validated local/open VLM adapter without changing the consumer API.
6. Expand Bihar and cross-government language packs.
