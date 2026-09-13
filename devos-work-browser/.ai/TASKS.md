# Tasks

## Core completed / verified
- F0 Windows shell + embedded WebView2 + navigation + URL/search resolution.
- F1 multi-tab browser core + persistent profile + downloads + session save/restore.
- F2 same-browser automation adapter.
- F3 structured execution + verification + bounded retry.
- F4 table extraction + CSV export.
- F5 checkpointed task engine + resume semantics.
- F6 constrained natural-language planner.
- F7 mutation approval policy.
- Synthetic 100-record portal fixture.
- 100-step recovery regression resumed from checkpoint 47.
- Windows CI restore/build/tests.
- Self-contained win-x64 publish artifact.

## Remaining acceptance before merge/release
- Interactive Windows launch and UX acceptance on a real desktop.
- Verify multiple tabs, profile/session persistence, downloads and browser navigation interactively.
- Run controlled automation against `test-portal/index.html` and confirm same-browser DOM control.
- Review PR #16 diff and merge only when explicitly desired.

## Deferred feature layers
PDF/image tooling, OCR, printing, FTP/SFTP/WebDAV/SMB, MCP, multi-agent, workflow recorder and complex desktop automation.
