# Windows Work Browser

**Full Chromium browser + AI work automation for Windows.**

## Product promise

The default application is a full-fledged Chromium browser. Users can browse, use compatible extensions, maintain profiles, tabs/windows, downloads, bookmarks, history, permissions, DevTools and printing without enabling the agent.

Automation is the second layer: the browser can observe and operate websites, while a policy-controlled Windows executor can operate native windows/dialogs, clipboard and printer workflows. External AI systems connect through MCP; they never receive arbitrary native command execution.

## Core capabilities

| Area | Capability |
|---|---|
| Browser | Chromium, tabs, profiles, extensions, downloads, DevTools |
| AI | Observe / understand / plan / validate / act / verify / recover |
| Web automation | Playwright / CDP / open-browser-use integration boundary |
| Desktop | Win32 / UI Automation / AutoHotkey adapter boundary |
| Files | Local + FTP / SFTP / WebDAV / SMB workspace model |
| PDF | OCR, merge, split, rotate, extract, compress, print |
| Images | Crop, deskew, resize, background removal, conversion, size targeting |
| Extraction | Tables, pagination, detail-record traversal, CSV/XLSX/JSON/PDF |
| Communication | Pluggable inbox/send providers with approval gate |
| Workflows | Record/replay, schedule, pause/resume, checkpoints, recovery |
| Security | Windows-backed vault, capability permissions, approval gates, evidence |
| External AI | MCP capability gateway for ChatGPT/Codex/Claude/Gemini/local agents |

## Typical task

> "Open the student list, visit every record, collect name/DOB/class, download available documents, and create an Excel file."

The agent should preview the plan, request approval only where policy requires it, execute browser actions, use native Windows actions when needed, checkpoint progress, verify record counts, produce requested files, and retain evidence without storing credentials in logs.

## Fast Windows delivery

Option A uses a verified BrowserOS Windows artifact as the browser foundation and attaches the product overlay through supported extension/MCP/native-messaging/service integration points. The reproducible full Chromium source build remains the fallback and release-audit lane.

## Workspace architecture

```text
browser-automation/windows-work-browser/
  app/                  # browser/workspace UI
  agent/                # orchestration, policy, tasks, evidence
  browser-control/      # Playwright/CDP/open-browser-use
  desktop-control/      # Windows/AHK/Win32
  mcp/                  # external AI gateway
  files/                # local + remote file workspace
  pdf/                  # PDF/OCR services
  image/                # image processing
  communications/       # messaging/email adapters
  workflows/            # reusable automation recipes
  vault/                # protected credential broker
  permissions/          # capability policy + approvals
  extraction/           # universal extract/export
  vendor/               # pinned upstream components
  docs/                 # requirements, ADRs, release evidence
  .ai/                  # durable DevOS project state
```

## Completion rule

A product capability is complete only when its implementation, security boundary, automated tests, Windows runtime evidence and documentation are present. A passing contract check alone does not make the product release-ready.

## Non-goals

- Do not turn the product into a headless automation-only browser.
- Do not expose arbitrary AI-generated AHK/shell/PowerShell/Playwright execution directly to Windows.
- Do not silently patch upstream binaries.
- Do not ship unverified third-party artifacts.
- Do not claim `RELEASED` without the release gates and evidence bundle.
