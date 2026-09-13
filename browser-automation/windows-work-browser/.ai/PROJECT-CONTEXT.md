# DevOS Project Context — Windows Work Browser

## Identity

Project: Windows Work Browser
Parent: `zzpsah/automation-suite`
Scope: Windows-first full Chromium browser with an optional AI automation layer.

## Governing principle

DevOS is the governance and durable-memory layer. The product source remains in Automation Suite. Do not move the product into the DevOS repository.

## Product contract

The default experience is a complete Chrome-class browser. AI automation must be optional and non-disruptive to ordinary browsing.

## Required execution paths

1. Browser DOM/semantics -> Playwright-compatible executor.
2. Existing signed-in browser -> open-browser-use extension/MCP adapter.
3. Windows/native UI -> validated desktop action -> AutoHotkey/Win32 executor.
4. Files/PDF/image/communication -> capability services.
5. External AI -> MCP gateway -> permission validator -> executor -> verifier.

## Required agent loop

Observe -> Understand -> Plan -> Validate -> Act -> Verify -> Recover -> Continue/Stop.

## Durable requirements

- Full Chromium browsing.
- Chrome-compatible extensions.
- Windows-first packaging.
- Multi-provider AI.
- Playwright web automation.
- open-browser-use extension retained for reusable real-browser control.
- AutoHotkey/Windows desktop automation.
- PDF/OCR/image processing.
- Local/file/FTP/SFTP/WebDAV browser.
- Embedded communication adapters.
- Universal extraction/export.
- Record/replay workflows.
- Scheduling/resume/recovery.
- Windows-secured credential vault.
- Capability permissions and human approval gates.
- Evidence/audit logging.

## Never claim

Never state that Chromium, Windows packaging, extension integration, desktop automation or end-to-end workflows are complete unless a reproducible build/test run and artifact evidence exist.

## Next state

Build foundation -> pin upstream revisions -> import/vendor reusable components -> Windows compile -> smoke test -> browser-control integration -> agent/MCP -> desktop adapter -> work tools -> release verification.
