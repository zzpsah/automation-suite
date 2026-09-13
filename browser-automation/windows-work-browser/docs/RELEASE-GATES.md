# Windows Work Browser — Production Release Gates

A release candidate is promotable only when every mandatory gate below has reproducible evidence.

| Gate | Requirement | Evidence |
|---|---|---|
| Browser foundation | Chromium-class Windows browser installs and runs | Windows CI + smoke artifact |
| Normal browsing | tabs, windows, profiles, history, downloads, extensions, DevTools | browser smoke suite |
| Browser control | Playwright/CDP/open-browser-use integration | control e2e |
| Agent | Observe→Understand→Plan→Validate→Act→Verify→Recover | orchestrator tests/evidence |
| Policy | capabilities, risk, approval and deny boundaries | policy tests |
| Native Windows | keyboard/mouse/window/dialog/print bridge | Windows native e2e |
| MCP | external agents can connect only through capability gateway | MCP integration tests |
| Extraction | pages, tables, pagination, detail records, exports | extraction fixtures |
| Files | local + FTP/SFTP/WebDAV flows | file integration tests |
| PDF | view/search/OCR/merge/split/export/print | PDF integration tests |
| Image | crop/deskew/resize/compress/upload | image integration tests |
| Communications | provider adapters with send approval | provider tests |
| Workflows | record/replay, schedule, pause/resume/recover | workflow tests |
| Vault | Windows-protected credential broker; raw secrets never exposed to model | vault security tests |
| Permissions | sensitive/destructive actions require approval | policy/e2e evidence |
| Security | no arbitrary AI-generated shell/AHK/Playwright execution | CI static + runtime tests |
| License/SBOM | upstream notices, AGPL obligations, dependency inventory | release package |
| Update/rollback | verified update, rollback and recovery path | Windows update test |
| Provenance | artifact/revision/patch/hash/build metadata retained | release manifest |

## Promotion states

`DEVELOPMENT → VERIFIED → RELEASE CANDIDATE → RELEASED`

A failed mandatory gate blocks promotion. A green documentation or contract check cannot substitute for missing runtime evidence.
