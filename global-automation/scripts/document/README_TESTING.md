# School Document Pipeline — Testing & Release Gate

The production pipeline is tested in layers. Tests must prove correctness without making test documents public.

## Test matrix

See [`production_test_matrix.json`](./production_test_matrix.json).

Required scenarios:

1. BSEB/admission document
2. Education Department document
3. DEO/DPO district document
4. scanned Hindi OCR fallback
5. duplicate submission
6. corrupt/unreadable input
7. contextual filename generation
8. safe publication

## Test layers

### Offline CI

No Supabase, B2 or Drive mutation. Validate Python compilation, imports, metadata helpers, filename rules, duplicate logic and safe failure behavior.

### Staging/integration

Use synthetic or explicitly designated test documents. Verify the complete worker chain without making a test record public.

### Production smoke test

Use one controlled real document only when operationally necessary. Verify intake → storage → processing → publication/archive, then inspect the resulting record. Never use student-sensitive material merely for testing.

## Release gate

A change is ready for production only when:

- offline tests pass;
- all regression cases pass;
- no secret is present in source;
- storage integrity remains intact;
- publication safety checks remain intact;
- existing successful documents remain readable;
- failure/recovery paths remain observable.

## Current OCR boundary

The School Document Pipeline currently uses its internal Tesseract Hindi+English OCR path. The separate Global Sarkari OCR project is not required for the current production test gate and must not be coupled into production until independently validated.
