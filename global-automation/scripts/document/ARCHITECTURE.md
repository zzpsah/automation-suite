# School Document Pipeline — Production Architecture

## Boundary

This pipeline is the production consumer-facing document system for the school. It currently uses the internal Tesseract Hindi+English OCR path. The separate Global Sarkari OCR project is an independently validated future provider and is not a production dependency today.

## Control plane

Supabase stores document metadata, lifecycle state, canonical identity, processing/publication state and audit information. It is not the primary binary file store.

## Storage plane

Backblaze B2 is primary binary storage. Google Drive is the backup/document-access layer. SHA-256 is used to verify file integrity. Storage failures must remain observable and retryable.

## Processing plane

The document processor extracts embedded PDF text when usable and otherwise renders/OCRs the document with Tesseract Hindi+English. It derives subject, authority, reference, date, category and descriptions while preserving raw OCR for audit/diagnostics.

## Lifecycle

`Received → Stored → Processing → Completed → Published`

Failure states remain explicit, including storage and processing failures. Publication is a separate controlled stage.

## Identity and versioning

Each document has a stable ID and checksum. `original_filename` is preserved. `display_filename` is contextual and human-readable. Reprocessing and superseding are stateful operations, not destructive replacement.

## Operations

Privileged operations are exposed through the authenticated `document-operations` Supabase Edge Function. The admin UI must not contain service-role credentials or bypass server-side authorization.

## Observability

Storage health, document pipeline health, recovery diagnostics, offline CI and production regression criteria are separate controls. A green worker run does not by itself prove document correctness; correctness is evaluated through metadata quality, lifecycle consistency and regression tests.

## Future Global OCR integration

When Global Sarkari OCR passes its own benchmark and release gates, it can replace or augment the OCR provider behind the processing interface. Consumer workflows should not need to know which OCR backend is active.
