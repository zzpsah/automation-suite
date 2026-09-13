# Windows AI Work Browser

A full-fledged Chromium browser for Windows with an integrated AI work/automation layer.

## Product rule

This is a **real browser first**. It must feel familiar to Chrome users. Desktop automation, AI agents, PDF, files, communication, extraction, and workflows are additional capabilities—not a replacement for normal browsing.

## Initial upstream references

- BrowserOS — Chromium/agentic browser foundation: https://github.com/browseros-ai/BrowserOS
- open-browser-use — real-browser control + MCP + Playwright-shaped SDK: https://github.com/open-browser-use/open-browser-use
- browser-use — agentic browser automation reference: https://github.com/browser-use/browser-use
- Noi — UI/workspace/reference ideas: https://github.com/lencx/Noi
- AutoHotkey — Windows desktop automation: https://github.com/AutoHotkey/AutoHotkey

Upstream code must be incorporated only after license/provenance review. Until then these are architecture references, not copied code.

## Target capabilities

- Chromium/Chrome-compatible browsing, tabs, profiles, extensions, bookmarks, history and downloads
- AI agent: observe → plan → act → verify → recover
- Playwright/browser automation
- AutoHotkey + Windows API desktop automation
- MCP gateway for ChatGPT/Codex/Claude/Gemini and other compatible agents
- Local encrypted credential vault
- Universal extraction/export: CSV/XLSX/JSON/PDF
- PDF viewer/OCR/merge/split/reorder/compress/sign/annotate/print
- Image/photo/signature processing for portal uploads
- Local/FTP/SFTP/WebDAV/cloud file browser
- Telegram/email and other communication connectors
- Workflow recorder/replay and scheduled jobs
- Permission center and human approval for sensitive actions
- Resumable jobs, evidence, verification and audit logs

## Execution boundary

AI never receives unrestricted shell or AutoHotkey execution. Actions go through:

`AI intent → validated action schema → policy/permission check → Playwright or desktop adapter → result → verification`

## Planned modules

```text
browser-automation/
├── app/                  # Windows application shell/integration
├── browser/              # Chromium/BrowserOS integration
├── agent/                # planner, observer, executor, verifier, recovery
├── playwright/           # web automation adapter
├── desktop/              # AutoHotkey + Windows API adapters
├── mcp/                  # external AI/MCP gateway
├── files/                # file manager + FTP/SFTP/WebDAV
├── pdf/                  # PDF pipeline
├── image/                # image/photo/signature pipeline
├── communications/       # Telegram/email/etc.
├── workflows/            # recorder, replay, scheduler, resumable jobs
├── vault/                # Windows-protected credential storage
├── permissions/          # policy and human approvals
├── extraction/           # universal extraction/export
├── ui/                   # Chrome-familiar workspace UI
├── docs/                 # architecture and decisions
└── .ai/                  # durable project state
```
