# DEVOS Work Browser — File Map

This module is intentionally isolated under `devos-work-browser/` while it is incubated inside `zzpsah/automation-suite`.

## Module boundary
All product code, tests, fixtures and product-specific durable context stay under `devos-work-browser/` unless a repository-level integration is genuinely required.

Repository-level integration:
- `.github/workflows/devos-work-browser-f0.yml` — Windows restore/build/test, self-contained win-x64 publish, packaged synthetic-fixture assertion, packaged-EXE startup smoke and artifact upload.

## Application
- `README.md` — current v0.1 core capabilities, commands and build notes.
- `ACCEPTANCE.md` — real Windows interactive acceptance checklist before merge/release.
- `Devos.WorkBrowser.sln` — .NET solution.
- `src/Devos.WorkBrowser.csproj` — Windows WPF/WebView2 application and packaged test-portal content rule.
- `src/App.xaml` / `src/App.xaml.cs` — application bootstrap.
- `src/MainWindow.xaml` / `src/MainWindow.xaml.cs` — browser shell, tab open/close host, profile/session lifecycle, downloads, navigation, packaged Test Portal entry point, DEVOS command bar, approval prompt, recoverable task execution and synthetic-portal acceptance command.

## Browser layer
- `src/Browser/UrlResolver.cs` — address vs search resolution.
- `src/Browser/SessionState.cs` — local session snapshot persistence.

## Automation/runtime
- `src/Automation/BrowserAutomationAdapter.cs` — same-browser WebView2 DOM control.
- `src/Runtime/AutomationModels.cs` — structured actions and adapter contract.
- `src/Runtime/ActionExecutor.cs` — execute, verify and retry loop.
- `src/Extraction/TableExtraction.cs` — table parser and CSV serializer.
- `src/Tasks/CheckpointStore.cs` — durable local step checkpoints and cleanup.
- `src/Tasks/ActiveTaskStore.cs` — persistent active task definition for restart recovery.
- `src/Tasks/TaskRunner.cs` — checkpoint-aware resume loop.
- `src/Tasks/SyntheticPortalWorkflow.cs` — real 100-record synthetic portal crawl, per-record checkpoint, resume and JSON/CSV export.
- `src/Planning/NaturalLanguagePlanner.cs` — constrained language-to-action planning, bounded semicolon sequences and approval policy.

## Tests and fixtures
- `tests/Devos.WorkBrowser.Tests.csproj` — xUnit tests.
- `tests/UrlResolverTests.cs` — URL/search regression tests.
- `tests/RuntimeTests.cs` — retry/checkpoint/active-task recovery tests.
- `tests/ExtractionTests.cs` — extraction/CSV tests.
- `tests/PlanningTests.cs` — planner, multi-step and approval-policy tests.
- `tests/SyntheticPortalWorkflowTests.cs` — real workflow regression proving interruption after record 47 and resume at record 48 through 100 with final JSON/CSV.
- `test-portal/index.html` — packaged synthetic 100-record student portal fixture.

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
When a standalone repository becomes available, move this module as a unit. Do not copy unrelated `automation-suite` modules. Preserve Git evidence where practical, then rerun Windows build/test/publish/fixture/startup verification in the new repository before continuing development.
