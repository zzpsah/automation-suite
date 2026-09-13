# Option A — Windows Artifact Delivery Lane

Option A is the fast delivery path: acquire a compatible upstream Windows artifact, verify provenance and SHA-256, then attach the Work Browser automation layer through supported integration points.

This does not replace the reproducible full Chromium source build. The full pinned build remains the fallback and release-audit lane.

## Pipeline

```text
release discovery -> Windows x64 artifact -> provenance check -> SHA-256 check
-> quarantine/stage -> launch smoke test -> Work Browser overlay
-> policy-controlled automation bridge -> evidence -> candidate package
```

## Mandatory artifact record

Record upstream project, immutable release/tag or source revision, platform/architecture, filename, download URL, SHA-256, acquisition time, verification result, overlay revision, and product build identifier.

If a trusted digest is unavailable, status remains `UNVERIFIED`; it cannot become a release candidate.

## Overlay rule

Do not silently patch the upstream browser binary. Prefer supported extension, agent, MCP, local service, native messaging, or documented integration points. Any binary patch must be explicitly reproducible, license-reviewed, and promoted to the full-build lane before release.

## Windows gates

- A1 Acquisition: Windows x64 artifact identified and downloaded.
- A2 Integrity: SHA-256 verified before execution.
- A3 Browser: launch, HTTPS render, tabs, profile/session persistence, downloads.
- A4 Overlay: agent surface, observation, Playwright/CDP, action contract and policy gate.
- A5 Evidence: artifact identity, product revision, test results, timestamps and artifact references; no secrets.

## Fallback

If the artifact is incompatible with the required Chromium revision, architecture, API surface, or security model, stop promotion and use the full pinned source build. Never bypass incompatibility with undocumented binary patching.

## Status

`OPTION-A-DESIGNED` — architecture/contracts are documented. A real Windows machine is still required for download, verification, launch, smoke tests, and promotion to `OPTION-A-VERIFIED` / `PRODUCT-READY`.
