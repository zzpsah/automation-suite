# Windows Build Gate

The Windows Work Browser build is considered **COMPILED** only when all gates below have machine-generated evidence.

## Gate A — source

- [ ] BrowserOS checkout exists.
- [ ] BrowserOS revision equals `8f5d36bc16f57115aeeff34baf4ad6aa964d509c`.
- [ ] open-browser-use revision equals `7765002ac88040aedc781be89afe68475a9d6c88`.
- [ ] SOURCE-MANIFEST.json is retained.

## Gate B — dependencies/legal

- [ ] Third-party dependency inventory generated.
- [ ] License inventory generated.
- [ ] AGPL-3.0 obligations for BrowserOS are reviewed for the distribution model.
- [ ] Required notices/source offer/corresponding-source packaging is implemented where applicable.

## Gate C — compile/package

- [ ] Windows Chromium toolchain configured.
- [ ] BrowserOS build completes with exit code 0.
- [ ] Installer/package generated.
- [ ] SHA-256 recorded for every distributable artifact.

## Gate D — runtime smoke test

- [ ] Application launches.
- [ ] New tab opens.
- [ ] HTTPS navigation works.
- [ ] Multiple tabs work.
- [ ] Profile/session persistence works.
- [ ] Extension loading works.
- [ ] Playwright/CDP control works.
- [ ] Native Windows automation bridge starts and is policy-gated.

## Gate E — evidence

Retain logs under the CI artifact/evidence system. A green documentation/contract CI job is **not** evidence of a successful Chromium compilation.

## Failure policy

If any gate fails, status remains `NOT COMPILED` or `BUILD FAILED` with the exact failing gate. Never convert a source-acquisition success into a runtime/build claim.
