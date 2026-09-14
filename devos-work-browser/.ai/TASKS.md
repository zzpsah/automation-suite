# Tasks

## Core v0.1 completed / verified
- F0 Windows shell + embedded WebView2 + navigation + URL/search resolution.
- F1 multi-tab browser core with open/close tabs, persistent profile, downloads and session save/restore.
- F2 same-browser automation adapter.
- F3 structured execution + verification + bounded retry.
- F4 table extraction + CSV serialization.
- F5 checkpointed task engine wired into the command execution path, with active-task persistence and restart recovery.
- F6 constrained command planner with bounded semicolon-separated sequences.
- F7 mutation approval policy plus fresh approval on recovery of interrupted committing tasks.
- DEVOS command bar wired into the active browser tab with `Ctrl+Space`, status/output and approval prompts.
- Packaged 100-record synthetic portal fixture and **Test Portal** entry point.
- `process synthetic portal` adapter-driven crawl/export workflow.
- Recovery acceptance regression: first run records 1-47, second fresh run records 48-100 only, final JSON + CSV contain all 100 records.
- Windows CI restore/build/tests.
- Self-contained win-x64 publish artifact.
- Packaged synthetic-portal presence verification.
- Packaged EXE startup smoke on Windows CI.

## Remaining acceptance before merge/release
- Perform `ACCEPTANCE.md` on a real interactive Windows desktop.
- Review PR #16 diff and merge only when explicitly desired.

## Deferred feature layers
PDF/image tooling, OCR, printing, FTP/SFTP/WebDAV/SMB, MCP, multi-agent, workflow recorder and complex desktop automation.
