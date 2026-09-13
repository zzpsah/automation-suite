# DEVOS Work Browser — Module AI Entry Point

This module is a clean scratch build of the DEVOS AI Work Browser for Windows. It is not the old BrowserOS overlay prototype and must not reuse that prototype as the primary UI or runtime.

## Scope now
Foundation first. Current milestone F0 is only: custom Windows shell, embedded Chromium-family browser, one tab, address/navigation controls, clean startup/shutdown, and build verification.

## Do not add yet
PDF/image suites, FTP/SFTP/WebDAV/SMB, MCP, multi-agent, printing, workflow recorder, OCR, complex desktop automation, or other feature work until the core browser/runtime milestones are verified.

## Engineering rules
1. Preserve project isolation from other automation-suite modules.
2. Prefer the smallest complete change.
3. Browser ownership and deterministic reliability come before AI features.
4. Future automation must use observe -> act -> verify -> checkpoint -> recover semantics.
5. Never claim completion without test/build evidence.
6. Never store credentials, cookies, tokens, private school data, or user secrets in Git.
7. Keep durable state under this module's `.ai/` directory.
