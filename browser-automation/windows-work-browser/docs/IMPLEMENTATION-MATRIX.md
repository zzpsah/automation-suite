# Implementation Matrix

| Area | Contract | Adapter/implementation | Runtime gate |
|---|---|---|---|
| Chromium browser | ✅ | BrowserOS Option A artifact | ✅ Windows CI foundation |
| Agent extension | ✅ | pinned BrowserOS extension | ✅ artifact integrity |
| Browser control | ✅ | Playwright/CDP adapter | ⏳ E2E |
| Native Windows | ✅ | Win32/UIA + AutoHotkey adapter | ⏳ E2E |
| MCP | ✅ | capability gateway | ⏳ E2E |
| Agent runner | ✅ | task runner + checkpoints | ⏳ integration |
| Universal extraction | ✅ | extractor service | ⏳ implementation |
| Files | ✅ | local/FTP/SFTP/WebDAV | ⏳ implementation |
| PDF/OCR | ✅ | PDF service | ⏳ implementation |
| Image processing | ✅ | image service | ⏳ implementation |
| Communications | ✅ | provider adapters | ⏳ implementation |
| Workflows | ✅ | recorder/replay/scheduler | ⏳ implementation |
| Credential vault | ✅ | Windows DPAPI/Credential Manager | ⏳ runtime security |
| Permissions | ✅ | policy + approval UI | ⏳ runtime security |
| Evidence | ✅ | action evidence store | ⏳ E2E |
| Update/rollback | ✅ | release manager | ⏳ Windows E2E |
| Licensing/SBOM | ✅ release gate | generator/package | ⏳ release |

## Product readiness rule

`VERIFIED` means the cited component/path has reproducible evidence. `RELEASE CANDIDATE` requires every mandatory row to have runtime evidence. `RELEASED` additionally requires signed packaging, update/rollback, license/SBOM, and final acceptance evidence.

## Design rule

Do not replace a full Chromium browser with a headless automation shell. Normal browsing stays first-class; automation is an optional capability layer.
