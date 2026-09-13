# OCR Continuous Improvement

This process is intentionally separate from the production OCR core and from consuming projects such as Telegram, Supabase, and school-data processing.

## Feedback loop

```text
Production OCR
  -> privacy-safe feedback/candidate
  -> frequency + consistency analysis
  -> candidate language-pack change
  -> regression test
  -> benchmark
  -> approved promotion
  -> new language-pack version
```

## What can be learned

- recurring OCR spelling variants
- authority aliases
- district/block aliases
- administrative terminology
- subject vocabulary

## What must not be learned automatically

- arbitrary names as official authorities
- dates or reference numbers
- credentials or secrets
- publication/approval decisions
- document text or raw scans in the training metadata

## Promotion rule

A candidate is never written directly into the stable language pack. It must have evidence, pass safety checks, receive approval, and gain a regression test. Rejected candidates remain audit information and are not runtime rules.

## Model training

Actual OCR model training is a separate later stage. The same reviewed corpus can eventually produce image/transcription datasets for alternative OCR backends, but a model is promoted only after benchmark comparison against the current backend.
