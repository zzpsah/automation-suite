# Windows Work Browser — Build Status

**Status: OPTION-A RUNTIME VERIFICATION IN PROGRESS**

This file deliberately prevents the project from being reported as production-ready without evidence.

## Current state

- Repository architecture: established
- Action/executor/policy/task/verification contracts: established
- Upstream/provenance registry: established
- BrowserOS Windows release artifact: pinned to `v0.50.3` x64 installer
- Upstream artifact SHA-256: `3ae8dc6cd7fa8c39760d8c95591147e283705ec7d6f1cc4b02561d2696ef86c7`
- Option A artifact bootstrap: implemented
- Option A Windows CI gate: implemented on repository root workflow
- First Windows Option A CI run: **SUCCESS** for acquisition/integrity/initial launch gate (run 1)
- Updated install-and-browser-launch gate: **QUEUED** (run 2)
- Full Chromium/BrowserOS source checkout: not required for Option A delivery, retained as fallback build lane
- Local Windows interactive desktop validation: not available from this integration environment

## Required evidence before candidate promotion

1. Windows runner downloads the exact pinned installer.
2. SHA-256 matches the upstream release digest.
3. Authenticode signature is valid.
4. Installer completes into an isolated target.
5. Installed browser executable is located and launches.
6. HTTPS/new-tab/tab-window/profile smoke tests pass.
7. Browser-control/MCP overlay smoke tests pass.
8. Native Windows bridge is policy-gated and verified.
9. Evidence artifacts and hashes are retained.
10. License/SBOM/release package is complete.

## Important distinction

A successful CI run proves only the gates executed by that run. It does **not** prove the entire Work Browser product is complete. The product remains below production-ready until browser-control, desktop automation, extraction, files/PDF, communications, workflows, vault/permissions, installer/update/rollback, and full integration evidence are green.

## Execution order

`pin -> acquire -> verify -> install -> launch -> browser-smoke -> overlay-smoke -> capability-e2e -> security -> license/SBOM -> release -> retain evidence`

No documentation-only success, unrelated CI success, or simulated result may be treated as product completion.
