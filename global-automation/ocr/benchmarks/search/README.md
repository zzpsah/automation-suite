# Search Golden Benchmark

P28 provides a sanitized, deterministic regression gate for global OCR retrieval.

## Coverage

- Hindi and mixed Hindi/English queries
- government reference/date terms
- top-k expected-document hit rate
- page/block provenance validity
- deterministic ordering across repeated runs

The benchmark consumes `SearchHit` results and does not rewrite source evidence.
Cluster-aware and timeline behavior is covered by the P27 contract tests; future
benchmark cases may add explicit cluster/date-range fixtures.

## Gate

The default release gate requires **>=95% top-k hit rate**, 100% provenance validity,
and deterministic ordering. The runner fails closed when a threshold is not met.

No benchmark is considered passed merely because these files exist; a release
must execute the benchmark and retain its result in CI/release evidence.
