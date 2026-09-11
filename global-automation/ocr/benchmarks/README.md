# Global OCR benchmarks

Benchmarks are release gates, not training side effects. A candidate backend/model/correction change must be evaluated against a reviewed corpus before promotion.

Track at minimum:
- character error rate (CER) where ground truth exists;
- word error rate (WER) where tokenization is reliable;
- field extraction accuracy;
- page-level weak/blank diagnostics;
- backend/runtime characteristics;
- regression count against the previous release.

Training jobs may produce candidate reports, but they never mutate runtime files or silently promote a model.
