# Tasks

## Core implemented
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

## Active final core gate
- Run final Windows CI on latest head.
- Verify restore/build/tests.
- Verify self-contained `win-x64` publish step and artifact upload.
- Update PR metadata with final evidence.

## Still required outside CI before product release
- Interactive Windows launch and UX acceptance on a real desktop.
- Confirm WebView2 runtime/profile behavior, downloads and tab/session restore interactively.
- Controlled browser automation acceptance against the synthetic portal.

## Explicitly deferred feature layers
PDF/image tooling, OCR, printing, FTP/SFTP/WebDAV/SMB, MCP, multi-agent, workflow recorder and complex desktop automation.
