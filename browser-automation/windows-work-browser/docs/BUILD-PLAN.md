# Build Plan — Windows Work Browser

## Definition of done

A release candidate is not considered complete until all of the following are demonstrated on Windows:

- Chromium browser launches and renders ordinary sites reliably.
- Tabs, windows, profiles, history, downloads, bookmarks, permissions and extensions work.
- Existing Chrome-class browsing remains usable with AI disabled.
- Agent can observe a page, plan an action, execute browser actions and verify the result.
- Playwright-compatible browser control works against the product browser.
- open-browser-use extension/MCP path can control a signed-in browser session.
- Desktop adapter can safely perform approved keyboard/mouse/window/file-dialog/clipboard actions.
- Browser and desktop actions share one task state machine and evidence log.
- MCP can expose approved capabilities to external agents.
- Human approval gates work for final submission, destructive actions, credentials/OTP and other policy-defined sensitive operations.
- PDF/image/file/FTP/communication tools have automated tests and integration paths.
- Universal extraction can traverse list/detail pages, resume interrupted jobs and produce CSV/XLSX/JSON/PDF.
- Workflows can be recorded, replayed, scheduled and recovered.
- Credentials are protected by Windows-native secure storage; plaintext secrets are never written to task logs.
- Windows installer, uninstall, update and rollback paths are tested.
- SBOM/license/provenance artifacts are generated.
- CI passes build, lint, unit, integration and security checks.

## Milestones

### M0 — Foundation
- Repository contract
- DevOS `.ai` state
- Upstream manifest
- License/provenance ledger
- Architecture/ADRs
- CI skeleton

### M1 — Chromium foundation
- Pin BrowserOS/Chromium revision
- Windows build bootstrap
- Branding/resources
- Browser smoke test
- Packaging artifact

### M2 — Browser control
- Playwright adapter
- open-browser-use extension adapter
- tab/session model
- observation/action/result contracts
- download/upload handling

### M3 — Agent + MCP
- planner
- policy validator
- executor
- verifier
- recovery loop
- MCP gateway
- external agent compatibility tests

### M4 — Windows desktop
- AHK command adapter
- Win32/window adapter
- clipboard
- native file dialogs
- printer integration
- foreground-window verification

### M5 — Work tools
- file manager
- FTP/SFTP/WebDAV
- PDF
- OCR
- image processor
- communication adapters

### M6 — Automation platform
- recorder/teach mode
- deterministic workflow runner
- AI recovery
- scheduler
- resumable jobs
- extraction/export

### M7 — Security + release
- credential vault
- capability permissions
- approvals
- audit/evidence log
- updater
- signing
- SBOM/license report
- Windows release candidate

## Architecture rule

The browser is the product. The automation layer is an opt-in capability layer attached to the browser. Browser automation and desktop automation are peer executors behind a common policy-controlled action interface.
