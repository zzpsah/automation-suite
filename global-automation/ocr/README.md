# Government Document Vision & OCR Platform

**Standalone shared OCR and government-document understanding layer.**

This component is deliberately independent of any one school, portal, bot, storage provider, database, or workflow. The School Document Pipeline is only one consumer. Future projects reuse this engine instead of copying OCR logic.

## DevOS recovery / source of truth

This README records the current architecture, implementation state, constraints, limitations and next steps. **When DevOS resumes work, read this file first, then inspect code/tests and recent commits before continuing.** Material implementation decisions must be documented here or in the nearest subsystem README during the same development sequence.

## Stable consumer API

```python
from ocr import process_file, process_pdf, process_image

result = process_file("document.pdf", "/tmp/ocr-work")
result = process_file("scan.jpg", "/tmp/ocr-work")
```

Consumers receive source-preserving full text, ordered page text, diagnostics, metadata, taxonomy and confidence. Backend internals remain private.

## Core architecture

```text
Government Document
        ↓
Image / Vision Processing
        ↓
OCR Backend Adapters
 ├── Tesseract
 ├── PaddleOCR
 └── Future VLM
        ↓
OCR text + geometry
        ↓
Region Alignment / Consensus
        ↓
Document Structure Intelligence
 ├── explicit blocks
 ├── global reading order
 ├── columns
 ├── headers / footers
 ├── tables
 ├── sections / annexures (planned)
 └── cross-page continuity (planned)
        ↓
Visual Artifact Intelligence
 ├── signature candidates
 ├── stamp / seal candidates
 └── annotation candidates
        ↓
Layout-preserving Reconstruction
        ↓
Document Understanding
 ├── metadata
 ├── classification
 ├── subject
 └── field confidence
        ↓
Consumer project
```

**Important:** OCR must not simply flatten a government document into a text blob. The target representation is **OCR → geometry → layout blocks → document structure → optimized reading order → formatted text/HTML/Markdown/JSON**. Original evidence remains preserved.

## Document structure intelligence

Implemented in `document_structure.py` and `reading_order.py`:

- explicit `DocumentStructure` and `StructureBlock` models
- deterministic page ordering
- geometry attached to structure blocks for downstream ordering
- page-level block generation from geometry-aware OCR spans
- column-aware block ordering
- conservative table recognition integration
- structural block labels such as header/footer/body/heading-or-label
- global reading-order optimizer for multi-page and mixed-layout documents
- headers are placed before page body content and footers after body content
- explicit column assignments are preferred; otherwise visual geometry is used
- JSON-safe serialization through `structure_to_dict()`

The structure model is intentionally evidence-preserving. It records what the layout engine inferred and its confidence; it does not rewrite OCR evidence or invent missing cells.

### Reading-order policy

`reading_order.py` provides `ReadingOrderBlock` and `optimize_reading_order()`.

The optimizer is deterministic and conservative:

1. process pages in numeric order
2. emit detected headers first
3. order body blocks top-to-bottom within explicit columns
4. for unassigned mixed layouts, infer visual column bands from geometry
5. emit footers last
6. use stable geometry/block IDs as tie-breakers

This is a **structure/routing heuristic**, not a claim that the inferred order is legally or semantically authoritative. Source OCR, page boundaries and original evidence remain unchanged.

Current limitation: the optimizer does not yet perform graph-based global reading-order inference, robust region adjacency optimization, or semantic section ordering. It also inherits the limitations of the baseline column and table detectors.

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

The image layer is backend-neutral. Tesseract currently performs candidate inference; PaddleOCR and future VLM implementations use the same backend contract. Optional backends must not become production dependencies merely because an adapter exists.

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

## Layout intelligence

Implemented under `global-automation/ocr/`:

- `region_alignment.py` — geometry-aware OCR span alignment.
- `region_consensus.py` — region disagreement/consensus diagnostics.
- `text_reconstruction.py` — line grouping, horizontal spacing and paragraph-aware reconstruction.
- `layout_intelligence.py` — column detection, conservative table-cell detection and structural block labels.
- `document_structure.py` — explicit page/block structure and geometry-aware structure model.
- `reading_order.py` — deterministic global reading-order optimization across page/column structure.

## Visual artifact intelligence

`vision_intelligence.py` provides conservative candidate labels for:

- signatures
- stamps/seals
- annotation areas

These are **routing/review signals only**. They are not authenticity, authorship, approval or legal-validity determinations. Current baseline uses OCR text/geometry heuristics; pixel-level visual classification belongs to a future optional vision backend.

## Multi-page intelligence

`multipage_intelligence.py` provides:

- page count
- repeated-header detection
- repeated-footer detection
- simple continuation signals

It preserves every page and does not synthesize missing content. Full section/annexure/attachment boundary intelligence is a future upgrade.

## Page preservation

PDF processing keeps ordered page text and privacy-safe page diagnostics. Consumers can identify blank/weak pages and retry or route them to another backend without losing the original evidence.

## Confidence and review

Field-aware confidence is separate from document-level confidence. Low-confidence fields can be routed for review without rewriting source OCR. Confidence is a decision-support signal, not proof of truth.

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

## Current implementation state

Implemented foundation:

- reusable OCR service/API
- image preprocessing and quality analysis
- Tesseract backend
- optional PaddleOCR adapter
- backend benchmark/selection policy
- multi-backend/page consensus
- line/region disagreement diagnostics
- field-aware confidence
- geometry-aware region alignment
- layout-preserving reconstruction
- column and conservative table intelligence
- explicit document structure model and global reading order
- signature/stamp/annotation candidate intelligence
- multi-page repeated-element intelligence
- separate image-processing benchmark foundation
- CER/WER benchmark metrics
- isolated training/improvement workflow
- DevOS recovery documentation

Not yet release-certified:

- real reviewed corpus at production scale
- calibrated benchmark results on representative Bihar government documents
- production-pinned PaddleOCR artifact
- pixel-level signature/stamp/seal vision model
- graph-based/global reading-order optimizer beyond the current deterministic geometry heuristic
- high-fidelity table reconstruction
- section/annexure/attachment boundary model
- cross-page entity/section continuity graph

## Release gates

A change is not considered production-ready merely because code exists. Release validation should cover:

1. unit/regression tests
2. image-processing regression benchmark
3. OCR CER/WER benchmark
4. Hindi + English + Sarkari terminology golden set
5. field-level confidence benchmark
6. structure-level benchmark, including reading-order cases
7. backend comparison where applicable
8. latency/resource checks
9. artifact version + SHA-256 verification
10. consumer API compatibility
11. source-evidence preservation

Never report a gate as passed without actual execution or verified CI evidence.

## Roadmap / next recovery point

1. Add explicit section, annexure, attachment and robust table schemas including merged/irregular cells.
2. Add multi-page structure graph and cross-page entity/section continuity.
3. Upgrade reading order from deterministic geometry heuristics to graph-based global optimization with robust region adjacency and mixed-layout handling.
4. Add pixel-aware optional vision backend for handwriting/signature/stamp/seal detection while preserving evidence-safe routing semantics.
5. Add real reviewed Bihar Education image/PDF corpus with provenance.
6. Add CER/WER, field-level and structure-level golden benchmarks.
7. Calibrate backend confidence and release policy.
8. Add pinned PaddleOCR production artifact once benchmarked.
9. Add validated local/open VLM adapter without changing the consumer API.
10. Expand Bihar and cross-government language packs.
