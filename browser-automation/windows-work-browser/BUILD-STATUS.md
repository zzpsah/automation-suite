# Windows Work Browser — Build Status

**Status: VERIFIED FOUNDATION / INTEGRATION BUILD**

This file is the authoritative engineering status. It never marks the product release-ready without product-level runtime evidence.

## Verified Windows foundation

- BrowserOS Windows x64 artifact pinned to `v0.50.3`.
- Upstream artifact SHA-256: `3ae8dc6cd7fa8c39760d8c95591147e283705ec7d6f1cc4b02561d2696ef86c7`.
- Download, SHA-256 and Authenticode verification passed in Windows CI.
- BrowserOS installer completed successfully.
- Browser launch passed.
- CDP endpoint and `https://example.com` navigation smoke passed.
- Agent extension artifact integrity passed.
- Evidence bundle retained as GitHub Actions artifact.

## Engineering contracts implemented

- AutomationAction capability/risk contract.
- Deterministic policy and approval gate.
- Capability-scoped executor registry.
- Browser Playwright/CDP/open-browser-use control contract.
- Windows-native operation contract.
- MCP capability gateway contract.
- Resumable task/checkpoint contract.
- Universal extraction and export contract.
- Local/FTP/SFTP/WebDAV/SMB file workspace contract.
- PDF and image processing contracts.
- Communication provider contract.
- Workflow record/replay/schedule/recovery contract.
- Permission Center contract.
- Windows-backed credential-vault/opaque lease contract.
- Update/rollback promotion contract.
- Redacted evidence/audit contract.
- Third-party license/SBOM release gate documentation.

## Integration work still required

1. Real Playwright adapter and browser-control E2E against the shipped browser.
2. MCP gateway implementation and external-agent interoperability tests.
3. Windows native adapter implementation (Win32/UI Automation/AutoHotkey) and E2E tests.
4. Extraction engine implementation including pagination/detail traversal, deduplication and source-count verification.
5. File browser and FTP/SFTP/WebDAV/SMB adapters.
6. PDF/OCR/image engines and portal upload preparation pipeline.
7. Communication provider adapters and send approval UX.
8. Workflow recorder/player, scheduler, checkpoint persistence and recovery.
9. DPAPI/Credential Manager implementation and permission enforcement.
10. Security/adversarial tests and secret-handling audit.
11. Generated SBOM, license notices and BrowserOS AGPL source-obligation package.
12. Verified update/rollback implementation.
13. Product UI overlay, Windows installer/update packaging and release branding.
14. Full Windows end-to-end acceptance suite.

## Promotion

`FOUNDATION-VERIFIED → INTEGRATION → RELEASE CANDIDATE → RELEASED`

The current state is **FOUNDATION-VERIFIED / INTEGRATION BUILD**. The browser foundation is proven; the complete Work Browser product is not yet release-ready.
