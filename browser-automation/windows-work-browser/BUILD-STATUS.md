# Windows Work Browser — Build Status

**Status: INTEGRATION VERIFIED / RELEASE CANDIDATE BLOCKED**

This file is the authoritative engineering status. It must only move to `RELEASE CANDIDATE` after every mandatory runtime gate has executable evidence.

## Verified Windows foundation

- BrowserOS Windows x64 artifact pinned to `v0.50.3`.
- Upstream artifact SHA-256: `3ae8dc6cd7fa8c39760d8c95591147e283705ec7d6f1cc4b02561d2696ef86c7`.
- Download, SHA-256 and Authenticode verification passed in Windows CI.
- BrowserOS installer completed successfully.
- Browser launch passed.
- CDP endpoint and `https://example.com` navigation smoke passed.
- Agent extension artifact integrity passed.
- Evidence bundle retained as GitHub Actions artifact.

## Verified engineering package

- TypeScript agent/runtime workspace compiles on Node 24.
- Agent typecheck, build and runtime tests passed in the latest successful Agent CI run.
- Capability-scoped Playwright semantic controller is implemented against Chromium CDP and pinned to Playwright Core `1.63.0`.
- Deterministic MCP gateway maps requests only to declared `AutomationAction` capabilities and preserves approval boundaries.
- Workspace-scoped local file adapter prevents path escape.
- Contract Gate passes structural, immutable-pin and security-invariant checks.

## Newly wired product proof

- Windows Option A lane now launches the shipped BrowserOS artifact and runs a real Playwright `connectOverCDP` semantic smoke against the running browser.
- Service security tests cover workspace path containment and MCP approval preservation.

## Mandatory product gates still open

1. Real BrowserOS extension installation/integration beyond artifact staging.
2. MCP transport/server interoperability with an external agent client.
3. Windows native Win32/UIA/AutoHotkey implementation + E2E.
4. Universal extraction engine with pagination/detail traversal, deduplication and count verification.
5. FTP/SFTP/WebDAV/SMB adapters.
6. PDF/OCR/image engines, including crop/deskew/background removal/upload preparation.
7. Communication providers with explicit send approval.
8. Workflow recorder/player, scheduler, checkpoint persistence and recovery.
9. DPAPI/Credential Manager runtime implementation.
10. Security/adversarial runtime tests for secret handling and capability isolation.
11. Generated SBOM + third-party notices + BrowserOS AGPL source-obligation package.
12. Verified update/rollback implementation.
13. Product UI overlay, branding and signed Windows installer/update package.
14. Full Windows end-to-end acceptance suite spanning the mandatory product path.

## Promotion rule

`FOUNDATION-VERIFIED → INTEGRATION → RELEASE CANDIDATE → RELEASED`

A successful browser foundation run does not imply that the Work Browser product is released. The release gate remains blocked until every mandatory product row has executable evidence.

## Current blocker summary

- Windows BrowserOS artifact/runtime foundation: **VERIFIED**
- Contract/security CI: **VERIFIED**
- Agent package: **BUILD + RUNTIME TEST VERIFIED**
- Playwright browser-control semantic E2E: **WIRED / AWAITING LATEST WINDOWS RUN**
- MCP/file integration foundation: **IMPLEMENTED / UNIT-TESTED**
- Remaining product runtime adapters: **NOT COMPLETE**
- Signed final installer: **NOT COMPLETE**
- Release: **NOT RELEASED**
