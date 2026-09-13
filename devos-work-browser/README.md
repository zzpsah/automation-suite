# DEVOS Work Browser

Windows-first custom work browser foundation: embedded Chromium-family browsing, deterministic same-tab automation, checkpoint/recovery, constrained command planning, approval gates, and a packaged synthetic acceptance portal.

## Current milestone: Core v0.1 release candidate

Implemented:

- custom .NET 8 WPF browser shell using Microsoft WebView2;
- multiple tabs with open/close controls;
- address/search bar, back, forward, reload and home;
- persistent WebView2 profile plus tab/session restore;
- downloads routed to `Downloads/DEVOS`;
- same-visible-tab DOM automation for click, type, read and wait;
- deterministic execute -> verify -> bounded retry runtime;
- checkpointed multi-step task execution with crash/restart recovery;
- constrained DEVOS command bar with `Ctrl+Space` focus and semicolon-separated bounded command sequences;
- explicit approval prompts for committing command categories;
- packaged 100-record synthetic student portal;
- `process synthetic portal` acceptance workflow that opens/reads all 100 records, checkpoints after each record, resumes from the saved record after interruption, and exports JSON + CSV;
- Windows CI restore/build/tests, self-contained win-x64 publish, packaged-fixture verification and packaged-EXE startup smoke.

## Core architecture

`DEVOS shell -> WebView2 browser -> automation adapter -> deterministic executor -> checkpoint/recovery -> task engine -> constrained planner`

The planner does not directly manipulate the browser. It produces structured actions and the deterministic runtime executes them against the active DEVOS tab.

## DEVOS command grammar

Examples:

```text
read #status
click #next
wait for #detail
type hello into #name
submit #save
click #next; wait for #students; read #status
process synthetic portal
```

`submit` is treated as a committing operation and requires explicit approval before execution. Unsupported commands fail visibly rather than being guessed.

## Synthetic acceptance flow

1. Click **Test Portal** to open the packaged fixture, or run `process synthetic portal` and DEVOS will load it when needed.
2. Run `process synthetic portal`.
3. DEVOS processes 100 synthetic student records through the same browser adapter.
4. After each record it saves a recovery checkpoint locally.
5. On completion it writes `students.json` and `students.csv` under `Downloads/DEVOS/SyntheticPortalExport`.

Automated regression explicitly interrupts after record 47 and verifies a fresh workflow resumes at record 48, processes through record 100, and exports all 100 records without reprocessing records 1-47.

## Technology

- .NET 8
- WPF
- Microsoft WebView2
- xUnit
- GitHub Actions on Windows

## Build

```powershell
dotnet restore devos-work-browser/Devos.WorkBrowser.sln
dotnet build devos-work-browser/Devos.WorkBrowser.sln -c Release
dotnet test devos-work-browser/tests/Devos.WorkBrowser.Tests.csproj -c Release
```

Self-contained publish:

```powershell
dotnet publish devos-work-browser/src/Devos.WorkBrowser.csproj -c Release -r win-x64 --self-contained true -o devos-work-browser/artifacts/win-x64
```

## Acceptance boundary

CI proves compilation, regression behavior, packaging, presence of the packaged synthetic portal, and non-immediate packaged-app startup failure. Visual correctness and human interaction quality still require the real-Windows checklist in `ACCEPTANCE.md` before merge/release.

## Deferred feature layers

PDF/image tooling, OCR, printing, FTP/SFTP/WebDAV/SMB, MCP, multi-agent, workflow recording and complex desktop automation are intentionally outside core v0.1.
