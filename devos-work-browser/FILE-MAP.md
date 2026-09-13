# DEVOS Work Browser — File Map

This module is intentionally isolated under `devos-work-browser/` while it is incubated inside `zzpsah/automation-suite`.

## Module boundary

All product code, tests, and product-specific durable context must stay under `devos-work-browser/` unless a repository-level integration is genuinely required.

Repository-level files currently related to this module:

- `.github/workflows/devos-work-browser-f0.yml` — Windows restore/build/test verification for the module.

## Product files

- `README.md` — product purpose, current scope, and run/build notes.
- `Devos.WorkBrowser.sln` — .NET solution.
- `src/Devos.WorkBrowser.csproj` — Windows WPF application project using WebView2.
- `src/App.xaml` / `src/App.xaml.cs` — application bootstrap.
- `src/MainWindow.xaml` / `src/MainWindow.xaml.cs` — F0 browser shell, navigation controls, and embedded WebView2 surface.
- `src/Browser/UrlResolver.cs` — strict address-vs-search interpretation for the address bar.

## Tests

- `tests/Devos.WorkBrowser.Tests.csproj` — xUnit test project.
- `tests/UrlResolverTests.cs` — address/search resolver regression tests.

## DevOS durable project context

- `AGENTS.md` — module-local AI/operator instructions and scope boundary.
- `.ai/PROJECT.md` — project identity and product objective.
- `.ai/CURRENT-STATE.md` — verified implementation state and current gate.
- `.ai/ARCHITECTURE.md` — current architecture and intended layer boundaries.
- `.ai/DECISIONS.md` — durable engineering decisions.
- `.ai/TASKS.md` — ordered next work; core first, features deferred.

## Current branch / PR

- Branch: `feat/devos-work-browser-core`
- Draft PR: `#16` (`Bootstrap DEVOS Work Browser F0`)

## Migration rule

When a standalone repository becomes available, move this module as a unit. Do not copy unrelated `automation-suite` modules. Preserve Git evidence where practical, then re-run Windows build/test verification in the new repository before continuing development.
