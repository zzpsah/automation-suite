# Government Document Intelligence v2

The OCR engine and government-document understanding are separate layers.

## Contract

`government_document.analyze_document(text, normalized_subject=None)` returns:

- `authority`: value + evidence source + confidence; header is preferred over body references.
- `subject`: official labelled subject when available; body paragraphs are not copied as the subject.
- `document_type`: evidence-based category and matching terms.
- `actions`: concise source lines containing actionable instructions.
- `deadlines`: source date strings found in the document.
- `short_description`: compact description derived only from extracted evidence.

No field is invented when evidence is absent.

## Design rule

A government document is not understood by OCR alone. The system first preserves raw OCR, then normalizes it, then extracts structured fields with evidence. This makes downstream school/portal consumers safer and allows later model backends to replace Tesseract without changing the contract.

## Current benchmark scope

The initial deterministic benchmark covers:

1. Header authority vs. body authority references.
2. Multi-line official subject extraction.
3. Admission/examination/transfer/service/training/scholarship/holiday classification.
4. Action and deadline extraction.
5. Short-description generation from evidence.

The benchmark is intentionally small until real reviewed government-letter samples are collected. It is not a claim of production accuracy across all Indian government documents.

## Next benchmark expansion

Add reviewed samples for Bihar Education Department, BSEB, BEPC, DEO/BEO/DPO offices, school circulars, orders, notifications, memoranda, notices and mixed Hindi/English scans. Record field-level expected values and evidence regions; never use raw document text as training metadata.
