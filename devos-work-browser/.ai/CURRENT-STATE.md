# Current State

Status: F0 in progress.

## Verified decisions
- Clean scratch module under `devos-work-browser/`.
- No reuse of the old BrowserOS overlay as primary UI/runtime.
- Windows-first implementation uses .NET 8 WPF + Microsoft WebView2.
- F0 scope is intentionally limited to custom shell + one embedded browser tab + navigation + startup/shutdown + build/test evidence.
- Browser automation, task runtime and AI layers remain future milestones.

## Evidence boundary
This state describes implementation intent and repository changes only. It is not proof of a successful Windows launch until Windows CI/build and later interactive acceptance succeed.
