# Composition Matrix

This matrix defines where each capability comes from and what must be implemented locally.

| Capability | Upstream/reference | Local product responsibility | Verification |
|---|---|---|---|
| Chromium browser | BrowserOS + Chromium | Pin revision, apply product patches, Windows packaging | Windows launch + navigation + tabs + profiles |
| Existing signed-in sessions | open-browser-use | Windows native-host/extension adapter | Attach to existing profile and complete safe test task |
| Deterministic web automation | Playwright | Typed executor + tracing + retries | E2E suite |
| Agent browser tasks | BrowserOS/browser-use | Agent loop + policy + verifier | Golden tasks with evidence |
| MCP | BrowserOS/open-browser-use/browser-use | Unified local gateway and capability registry | MCP contract tests |
| Windows desktop | Win32 + AutoHotkey | Typed desktop executor | Calculator/Notepad/file-dialog smoke tests |
| File operations | OS APIs | Permission-scoped file executor | Read/write/rename/delete approval tests |
| PDF | PDF MCP references + local libraries | Stable PDF service API | Merge/split/OCR/export tests |
| Image processing | Local libraries | Upload preprocessing pipeline | Dimension/format/size validation tests |
| Extraction | Browser DOM + browser-use patterns | Schema, pagination, resume, dedupe, export | Fixture-based extraction tests |
| Communication | Provider APIs/connectors | Provider adapters + send approval | Mock/provider integration tests |
| FTP/SFTP/WebDAV | Protocol libraries | Credential-scoped adapters | Upload/download/checksum tests |
| Vault | Windows credential/security APIs | Secret broker; no plaintext model exposure | Secret-handling tests |
| Workflows | Local engine | Record/replay/schedule/resume/recovery | Interrupted-run resume tests |
| Evidence | Local audit model | Screenshots, traces, action/result records | Evidence completeness checks |
| Installer/update | Windows packaging | Signed installer + rollback/update path | Clean-machine install test |

## Non-negotiable boundary

No upstream agent is permitted to invoke arbitrary shell, PowerShell, AHK or raw browser protocol without passing through the local policy validator.

## Product modes

- **BROWSE** — browser only; no agent execution unless explicitly invoked.
- **ASSIST** — agent can inspect and suggest actions; user controls execution.
- **AUTOMATE** — agent executes approved typed actions and verifies each step.

## Completion gate

A capability is not marked complete merely because its upstream exists. It is complete only after:

1. pinned source/version is recorded;
2. local adapter compiles;
3. unit/integration tests pass;
4. Windows smoke test passes where applicable;
5. evidence is retained;
6. security/permission checks pass;
7. build artifact is reproducible enough to be rebuilt by CI.
