# Option A — Verified Windows Artifact Lane

Option A is the fast delivery path for Windows Work Browser: use a compatible upstream BrowserOS Windows installer, verify immutable provenance and SHA-256, install it in an isolated staging target, then attach the Work Browser automation layer through supported extension/MCP/native-messaging/service integration points.

## Promotion gates

1. **A1 — Acquire:** exact release, asset URL, architecture and upstream revision recorded.
2. **A2 — Integrity:** SHA-256 matches the pinned manifest and Authenticode signature is valid.
3. **A3 — Install/launch:** isolated Windows installation succeeds and the browser remains running after launch.
4. **A4 — Overlay:** product integration is deployed without binary patching and capability boundaries remain policy-gated.
5. **A5 — Evidence:** logs, hashes, versions and smoke-test results are retained.

Missing digest, failed signature, or failed smoke test means **REJECTED**. A documentation-only green CI check is never runtime proof.

## Current pinned artifact

See `OPTION-A-RELEASE.json` for BrowserOS v0.50.3 x64 installer provenance and SHA-256.

## Security rule

AI plans may not execute arbitrary PowerShell, shell, AHK or Playwright. All product actions pass through the AutomationAction contract and policy engine.
