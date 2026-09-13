# DEVOS Work Browser — File Map

This module is intentionally isolated under `devos-work-browser/` while it is incubated inside `zzpsah/automation-suite`.

## Module boundary
All product code, tests, fixtures and product-specific durable context stay under `devos-work-browser/` unless a repository-level integration is genuinely required.

Repository-level integration:
- `.github/workflows/devos-work-browser-f0.yml` — Windows restore/build/test plus self-contained win-x64 publish artifact.

## Application
- `README.md` — product purpose and build notes.
- `Devos.WorkBrowser.sln` — .NET solution.
- `src/Devos.WorkBrowser.csproj` — Windows WPF/WebView2 application.
- `src/App.xaml` / `src/App.xaml.cs` — application bootstrap.
- `src/MainWindow.xaml` / `src/MainWindow.xaml.cs` — browser shell, tab host, profile/session lifecycle, downloads and navigation.

## Browser layer
- `src/Browser/UrlResolver.cs` — address vs search resolution.
- `src/Browser/SessionState.cs` — local session snapshot persistence.

## Automation/runtime
- `src/Automation/BrowserAutomationAdapter.cs` — same-browser WebView2 DOM control.
- `src/Runtime/AutomationModels.cs` — structured actions and adapter contract.
- `src/Runtime/ActionExecutor.cs` — execute, verify and retry loop.
- `src/Extraction/TableExtraction.cs` — table parser and CSV serializer.
- `src/Tasks/CheckpointStore.cs` — durable local task checkpoints.
- `src/Tasks/TaskRunner.cs` — checkpoint-aware resume loop.
- `src/Planning/NaturalLanguagePlanner.cs` — constrained language-to-action planning plus approval policy.

## Tests and fixtures
- `tests/Devos.WorkBrowser.Tests.csproj` — xUnit tests.
- `tests/UrlResolverTests.cs` — URL/search regression tests.
- `tests/RuntimeTests.cs` — retry/checkpoint/recovery tests, including resume from record 47 in a 100-step task.
- `tests/ExtractionTests.cs` — extraction/CSV tests.
- `tests/PlanningTests.cs` — planner and approval-policy tests.
- `test-portal/index.html` — synthetic 100-record student portal fixture.

## DevOS durable context
- `AGENTS.md`
- `.ai/PROJECT.md`
- `.ai/CURRENT-STATE.md`
- `.ai/ARCHITECTURE.md`
- `.ai/DECISIONS.md`
- `.ai/TASKS.md`

## Current branch / PR
- Branch: `feat/devos-work-browser-core`
- Draft PR: `#16` (`Build DEVOS Work Browser core`)

## Migration rule
When a standalone repository becomes available, move this module as a unit. Do not copy unrelated `automation-suite` modules. Preserve Git evidence where practical, then rerun Windows build/test/publish verification in the new repository before continuing development.
