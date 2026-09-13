# Upstream Lock / Provenance

This file is the durable registry for reusable external components. DevOS must consult it before introducing a duplicate implementation elsewhere.

| Component | Upstream | Role | License | Current status | Reuse rule |
|---|---|---|---|---|---|
| Chromium/browser foundation | `browseros-ai/BrowserOS` | Windows Chromium + agent/browser architecture | AGPL-3.0 | Pinned revision required before vendor import | Keep source/provenance isolated; preserve license notices |
| Real-browser control | `open-browser-use/open-browser-use` | MV3 extension, native bridge, MCP, Playwright-shaped SDK | MIT | Reusable; Windows support must be validated | Preserve upstream license + third-party notices |
| Browser agent reference | `browser-use/browser-use` | Agent/extraction/workflow reference | MIT | Reference/integration candidate | Reuse only after API/license audit |
| Browser workspace reference | `lencx/Noi` | UI/workspace ideas and reusable components where permitted | Audit required | Reference | Do not copy without license/provenance check |
| Windows desktop | `AutoHotkey/AutoHotkey` | Keyboard/mouse/window/native automation | Audit current release | Adapter dependency | Do not expose arbitrary scripts to the model |

## Pinning requirements

Every vendored component must record:

- upstream URL
- exact commit/tag/release
- license
- copyright/NOTICE files
- local patches
- reason for local patch
- Windows compatibility status
- build/test command
- checksum where release artifacts are consumed
- upgrade procedure

## Important licensing note

BrowserOS is currently AGPL-3.0 and includes Chromium/third-party licensing. open-browser-use is currently MIT. This project must preserve upstream obligations and must not imply that the combined product is covered by one license. A release build requires a generated third-party license/SBOM report.

## Reuse by future projects

DevOS should treat this registry as the authoritative reusable-component catalog. Future Automation Suite projects should depend on these adapters/components instead of independently reimplementing browser control.
