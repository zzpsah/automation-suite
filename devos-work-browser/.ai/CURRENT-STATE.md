# Current State

Status: core implementation advancing on `feat/devos-work-browser-core`.

## Verified foundation
- F0 custom Windows shell is implemented with .NET 8 WPF + Microsoft WebView2.
- Exact branch head `4b3f06ba8d74449d4f6f311bfc5a5ef9b2bb9ee2` passed Windows CI run `34774126122` (restore, build and tests all successful).
- F0 therefore has build/test evidence. Interactive Windows acceptance remains separate.

## Current implementation slice
- F1: multi-tab host, shared persistent WebView2 profile, DEVOS download directory, session snapshot persistence.
- F2: same-browser WebView2 automation adapter for click/type/read/wait/table extraction.
- F3: deterministic action executor with verification and bounded retry.
- F4: table extraction parser + CSV serialization.
- F5: checkpoint store + task runner that resumes from the last completed step.

These F1-F5 changes are implementation evidence only until the new branch head passes CI.

## Boundaries
- `main` remains untouched by this work.
- AI planner, complex mutation, PDF/image tooling, OCR, printing, FTP/SFTP/WebDAV/SMB, MCP and multi-agent remain deferred.
- No claim of live portal automation is made until interactive browser acceptance is performed.
