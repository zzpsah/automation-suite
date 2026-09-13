# Windows AI Work Browser Architecture

## 1. Product boundary

The product is a full Chromium browser for Windows. Normal browsing must work independently of AI services. AI/automation is an integrated capability layer.

## 2. Core runtime

```text
Windows
  │
  ├── Chromium browser runtime
  │     ├── tabs/windows
  │     ├── profiles/cookies
  │     ├── extensions
  │     ├── downloads
  │     └── print/PDF
  │
  └── Automation runtime
        ├── Agent Orchestrator
        ├── Playwright Adapter
        ├── Desktop Adapter (AHK/WinAPI)
        ├── MCP Gateway
        ├── File/PDF/Image services
        ├── Communications
        └── Workflow Engine
```

## 3. Agent loop

`Observe → Understand → Plan → Act → Verify → Recover → Continue`

Browser actions should prefer DOM/accessibility/semantic Playwright operations. Desktop actions are used for native dialogs, Windows applications, clipboard, printer, window management, and situations where browser-level control is insufficient.

## 4. External AI control

MCP is the controlled boundary:

```text
ChatGPT / Codex / Claude / Gemini / local agent
                    │
                    ▼
               MCP Gateway
                    │
             Action Schema
                    │
             Policy Engine
          ┌─────────┴─────────┐
          ▼                   ▼
      Playwright          Desktop Adapter
          │                   │
       Chromium        AutoHotkey/WinAPI
```

The gateway exposes capability-scoped tools rather than arbitrary code execution.

## 5. Desktop action safety

Never execute unrestricted model-generated AHK, PowerShell, CMD, or Python. The desktop adapter accepts validated commands such as:

- activate window
- hotkey
- key press/type
- mouse click at approved target
- clipboard read/write
- open/save dialog interaction
- printer selection
- launch approved application

Destructive, financial, authentication/OTP, final submission, and sensitive messaging actions can require human approval.

## 6. Universal extraction

```text
Page/List
   ↓
Record detector
   ↓
Field schema
   ↓
Pagination/detail traversal
   ↓
State checkpoint
   ↓
Validation
   ↓
CSV / XLSX / JSON / PDF
```

Jobs must be resumable and report detected records, extracted records, failures, duplicates, and missing fields.

## 7. Windows-first tools

The browser workspace will include Files, PDF, Images, Communications, Tasks, Vault, and Automate surfaces without sacrificing the normal browser navigation model.

## 8. Upstream integration strategy

BrowserOS is the primary Chromium/agent architecture candidate. open-browser-use is the primary reference for real-browser MCP control and its Playwright-shaped SDK. browser-use is an agent orchestration reference. Noi is a UI/workspace reference. AutoHotkey is the desktop automation adapter candidate.

Large upstream repositories should not be blindly copied into this monorepo. We will vendor/fork only after checking license compatibility, provenance, build reproducibility, and the exact integration boundary. Where practical, upstream projects remain pinned references or dedicated forks so updates can be tracked cleanly.
