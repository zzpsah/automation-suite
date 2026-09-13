# Implementation Matrix

| Area | Contract | Adapter/implementation | Runtime gate |
|---|---|---|---|
| Chromium browser | ✅ | BrowserOS Option A artifact | ✅ Windows CI foundation |
| Agent extension | ✅ | pinned BrowserOS extension | ✅ artifact integrity |
| Browser control | ✅ | bounded browser-control + CDP/Playwright adapter | 🟡 browser foundation E2E; semantic task E2E pending |
| Native Windows | ✅ | bounded Win32/UIA + AutoHotkey interface | ⏳ real Windows E2E |
| MCP | ✅ | capability gateway | ⏳ policy→executor→verify E2E |
| Agent runner | ✅ | task runner + checkpoints + runtime coordinator | ✅ typecheck/build/runtime tests |
| Universal extraction | ✅ | extraction planner + extractor service contract | ⏳ implementation E2E |
| Files | ✅ | local/FTP/SFTP/WebDAV/SMB service contract | ⏳ implementation E2E |
| PDF/OCR | ✅ | PDF service contract | ⏳ implementation E2E |
| Image processing | ✅ | crop/deskew/resize/background/size contract | ⏳ implementation E2E |
| Communications | ✅ | provider service contract with send approval | ⏳ provider E2E |
| Workflows | ✅ | trigger/run/pause/resume/cancel contract + examples | ⏳ runtime E2E |
| Credential vault | ✅ | Windows DPAPI/Credential Manager contract | ⏳ runtime security |
| Permissions | ✅ | deterministic policy + approval contract | ✅ contract gate |
| Evidence | ✅ | schema-aware redaction + evidence sink contract | ✅ contract/runtime package tests |
| Update/rollback | ✅ | release manager contract | ⏳ Windows E2E |
| Licensing/SBOM | ✅ release gate | release register/package contract | ⏳ generated release bundle |

## Verified infrastructure

- Option A Windows artifact acquisition/integrity/install/launch/CDP foundation has reproducible CI evidence.
- Agent package typecheck, build and runtime tests pass in GitHub Actions.
- Contract Gate passes structural, upstream-pin and security invariants.
- Canonical browser-control, native, MCP, extraction, permission, vault, evidence and update contracts are present.
- Capability catalog and example workflows are defined.

## Product readiness rule

`VERIFIED` means the cited component/path has reproducible evidence. `RELEASE CANDIDATE` requires every mandatory row to have runtime evidence. `RELEASED` additionally requires signed packaging, update/rollback, license/SBOM, and final acceptance evidence.

## Design rule

Do not replace a full Chromium browser with a headless automation shell. Normal browsing stays first-class; automation is an optional capability layer.
