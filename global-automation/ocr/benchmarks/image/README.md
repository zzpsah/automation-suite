# Image Processing Benchmark

The Government Document Vision & OCR Platform keeps image-processing evaluation separate from OCR and document-understanding evaluation.

## Goals

Measure whether preprocessing reliably improves document images and whether those improvements help downstream OCR.

### Benchmark dimensions

- orientation / rotation
- residual skew after deskew
- resolution and bounded upscaling
- contrast and faded scans
- scan noise and compression artifacts
- blur
- uneven background / shadows
- perspective distortion
- Hindi Devanagari scans
- mixed Hindi + English + numbers
- tables and dense forms
- stamps or marks overlapping text
- old photocopies
- multi-page documents

## Evaluation model

Each benchmark case should contain a source image plus optional ground truth and expected degradation metadata. A run records deterministic image-quality measurements before and after processing, then optionally records downstream OCR CER/WER.

Image-quality metrics are diagnostic signals, not claims of OCR accuracy. OCR accuracy is measured separately against verified ground truth.

## Recommended corpus layout

```text
image/
  dataset/
    clean/
    degraded/
    real/
  manifests/
    cases.jsonl
  results/
```

Large real documents and generated datasets should live outside Git when appropriate. Git should retain manifests, small fixtures, benchmark code, expected metrics, and release reports.

## Release gate

A production OCR release should not be promoted solely because an image metric improved. The release gate should combine:

1. image-processing regression checks;
2. OCR CER/WER regression checks;
3. Hindi/Sarkari golden-set checks;
4. latency/resource checks where required.

No benchmark result should silently change runtime behavior.
