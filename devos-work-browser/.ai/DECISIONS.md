# Decisions

## 2026-09-13 — Foundation-first rebuild
- Build a clean module; do not make the old BrowserOS overlay the product shell.
- Use .NET 8 WPF for the Windows application shell.
- Use Microsoft WebView2 as the embedded Chromium-family browser engine for F0.
- Keep the first milestone intentionally tiny: one tab, navigation, URL/search resolution, startup/shutdown and Windows build/test evidence.
- Defer AI and feature breadth until deterministic browser control and recovery foundations are proven.
