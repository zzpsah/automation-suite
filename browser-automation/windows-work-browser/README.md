# Windows Work Browser

A full Chromium browser for Windows with an optional AI work/automation layer.

## Product contract

- Normal mode must feel like a complete Chrome-class browser.
- AI is an optional superpower, not a replacement for browsing.
- Web automation uses Playwright-compatible browser control.
- Existing signed-in browser control is supported through the reusable open-browser-use extension/MCP component.
- Desktop automation is a separate Windows adapter using AutoHotkey and Windows APIs.
- ChatGPT/Codex/Claude/Gemini/local agents connect through a capability-gated MCP gateway.
- Files, PDF, image processing, communications, FTP/SFTP, extraction/export and workflows are first-class tools.
- Sensitive/destructive actions are policy-controlled and can require human approval.

## Upstream strategy

BrowserOS is the Chromium/agent reference and primary browser foundation candidate. open-browser-use is retained as a reusable browser-control component/reference. Browser Use and Noi are reference components where their licenses and implementation permit reuse. We do not blindly concatenate repositories; each upstream is pinned, provenance-documented, license-audited, and isolated so it can be reused by future Automation Suite projects.

## Workspace

```text
browser-automation/windows-work-browser/
  app/                  # product-specific browser/agent UI
  agent/                # observe/plan/act/verify/recover orchestration
  browser-control/      # Playwright + open-browser-use integration
  desktop-control/      # Windows/AHK adapter
  mcp/                  # external AI control gateway
  files/                # local/FTP/SFTP/WebDAV abstraction
  pdf/                  # PDF/OCR/merge/split/export services
  image/                # crop/deskew/resize/compress/background tools
  communications/       # Telegram/email/provider adapters
  workflows/            # record/replay/schedule/resume engine
  vault/                # Windows-protected credential broker
  permissions/          # capability/policy/approval engine
  extraction/           # universal extraction/export
  vendor/               # pinned reusable upstream components
  docs/                 # requirements, architecture, provenance, ADRs
  .ai/                  # durable DevOS project state
```

## Build phases

1. Governance + provenance + requirements.
2. Browser foundation and Windows build pipeline.
3. Browser-control bridge and extension.
4. Agent orchestration and MCP.
5. Desktop automation adapter.
6. Files/PDF/image/communications.
7. Universal extraction and workflows.
8. Credential vault and permission center.
9. Windows installer/update/signing.
10. Full integration/e2e verification.

## Non-goals

- Do not turn the product into a headless automation-only browser.
- Do not expose arbitrary AI-generated AHK/shell code directly to Windows.
- Do not claim a feature is complete without a reproducible build/test/evidence record.
