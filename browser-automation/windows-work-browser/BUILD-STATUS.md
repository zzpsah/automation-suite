# Windows Work Browser — Build Status

**Status: OPTION-A RUNTIME VERIFICATION IN PROGRESS**

This file deliberately prevents the project from being reported as production-ready without evidence.

## Current state

- Repository architecture: established
- Action/executor/policy/task/verification contracts: established
- Windows-native executor boundary: established
- MCP gateway boundary: established
- Universal extraction/resume contract: established
- Permission Center contract: established
- Credential vault/opaque lease contract: established
- Upstream/provenance registry: established
- BrowserOS Windows release artifact: pinned to `v0.50.3` x64 installer
- Upstream artifact SHA-256: `3ae8dc6cd7fa8c39760d8c95591147e283705ec7d6f1cc4b02561d2696ef86c7`
- Option A artifact bootstrap: implemented
- Option A Windows CI gate: implemented on repository root workflow
- Previous Windows Option A run: **BLOCKED AT INSTALLER** — download, SHA-256, and Authenticode passed; the installer invocation did not exit before cancellation and browser launch was skipped.
- Installer gate was corrected to use Chromium-style `/silent /install`, prevent automatic browser launch, use a 90-second bounded wait, and verify the actual `%LOCALAPPDATA%\BrowserOS\Application` install path.
- New runtime verification is required after the installer-gate correction; no success is claimed yet.
- Full Chromium/BrowserOS source checkout: not required for Option A delivery, retained as fallback build lane
- Local Windows interactive desktop validation: not available from this integration environment

## Required evidence before candidate promotion

1. Windows runner downloads the exact pinned installer.
2. SHA-256 matches the pinned release digest.
3. Authenticode signature is valid.
4. Installer completes using a bounded, reproducible invocation.
5. Installed BrowserOS executable is located at the expected Windows path and launches.
6. HTTPS/new-tab/tab-window/profile smoke tests pass.
7. Browser-control/CDP/MCP overlay smoke tests pass.
8. Native Windows bridge is policy-gated and verified.
9. Evidence artifacts and hashes are retained.
10. License/SBOM/release package is complete.
11. Update/rollback behavior is verified.
12. End-to-end product gates for extraction, files/PDF, communications, workflows, vault, permissions, security, and recovery are green.

## Important distinction

A successful CI run proves only the gates executed by that run. It does **not** prove the entire Work Browser product is complete. The product remains below production-ready until browser-control, desktop automation, extraction, files/PDF, communications, workflows, vault/permissions, installer/update/rollback, and full integration evidence are green.

## Execution order

`pin -> acquire -> verify -> install -> launch -> browser-smoke -> browser-control -> MCP -> native -> extraction -> files/PDF -> workflows -> vault/permissions -> security -> license/SBOM -> update/rollback -> release -> retain evidence`

No documentation-only success, unrelated CI success, or simulated result may be treated as product completion.
