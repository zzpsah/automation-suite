# DEVOS Work Browser

A clean Windows-first browser foundation for a future AI work browser.

## Current milestone: F0

Only these capabilities belong in F0:

- custom DEVOS Windows application shell;
- embedded Chromium-family browser using Microsoft WebView2;
- one browser tab;
- address bar;
- back, forward, reload and home navigation;
- URL/search normalization;
- clean startup and shutdown;
- Windows CI build and core unit tests.

Everything else is deliberately postponed until the browser foundation is verified.

## Architecture direction

The long-term stack is:

`DEVOS shell -> browser core -> controlled browser automation -> deterministic runtime -> verification/checkpoint/recovery -> task engine -> natural-language planner`

AI does not directly own the browser. The deterministic runtime owns execution; AI will later produce structured plans for that runtime.

## Technology

- .NET 8
- WPF
- Microsoft WebView2 (Chromium-based Edge runtime)
- xUnit for core unit tests

## Build

```powershell
dotnet restore devos-work-browser/Devos.WorkBrowser.sln
dotnet build devos-work-browser/Devos.WorkBrowser.sln -c Release
```

A successful build proves compilation only. Windows interactive acceptance remains a separate gate.
