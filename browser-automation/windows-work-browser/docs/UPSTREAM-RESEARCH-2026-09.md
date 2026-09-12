# Upstream Research — 2026-09

## Decision

Use a **layered composition strategy**, not a blind repository merge.

### Tier 1 — Browser foundation
- **browseros-ai/BrowserOS** — primary Chromium/agent architecture reference and candidate browser foundation.
  - Current upstream states Windows support.
  - Chromium fork/build system lives under `packages/browseros`.
  - Agent platform includes MCP/server, extension UI, CLI and browser control pieces.
  - License: AGPL-3.0.
  - Browser source build requires a large Chromium build environment; do not claim a local build until a Windows artifact and smoke test exist.

### Tier 2 — Real signed-in browser control
- **open-browser-use/open-browser-use** — reusable browser-control architecture.
  - MV3 extension + native host + Rust broker + TypeScript SDK + MCP.
  - Supports WebExtension and CDP backends.
  - Local capability/guard policy model is useful for our action-policy boundary.
  - Current public preview is macOS/Linux, so Windows support is an adaptation/validation task for this product.
  - License: MIT.

### Tier 3 — Agent/extraction reference
- **browser-use/browser-use** — reference/integration candidate for high-level browser agents, extraction and MCP.
  - Supports Playwright/Chromium workflows and MCP.
  - License/API must be pinned and audited before vendoring code.

### Tier 4 — Desktop automation
- **AutoHotkey/AutoHotkey** — Windows keyboard/mouse/window automation reference/dependency.
  - Use only behind a typed capability adapter.
  - Never execute arbitrary model-generated scripts directly.
  - Exact license/revision must be pinned before vendor import.

### Tier 5 — PDF capability
- **paradyno/PDF-MCP-Server** — Windows-capable PDF MCP implementation reference.
  - Provides PDF processing through an MCP interface and publishes Windows x64 binaries.
  - Useful as an integration/reference layer rather than a reason to duplicate our PDF API.
  - Audit its transitive dependencies and license obligations before reuse.

- **nfsarch33/pdf-mcp-server** — richer PDF/AI reference covering forms, OCR, redaction, signatures, table extraction and batch processing.
  - Contains AGPL-licensed dependencies; treat as reference unless the final distribution model is compatible.

### Tier 6 — Product/UI reference
- **ahamSel/WebPilot** — local-first Electron/Next.js agent-browser reference with Playwright MCP, multiple model providers and local run recording.
  - Use for UX/observability ideas only unless a component is explicitly license-compatible.

## Integration rule

The Windows Work Browser should expose one internal capability API:

```text
Agent intent
  -> typed action
  -> policy validation
  -> executor
     -> Browser executor (Playwright / OBU / CDP)
     -> Desktop executor (Win32 / AHK)
     -> File executor
     -> PDF executor
     -> Image executor
     -> Communication executor
  -> verification
  -> evidence/audit event
```

External projects are adapters/providers. They are **not** allowed to bypass `agent/action-contract.ts`.

## Licensing rule

Do not combine AGPL, GPL, MIT, Apache-2.0 and other upstreams into one undifferentiated source tree without a license review. Every imported component must retain its license and attribution. Release builds must generate a third-party/SBOM report.

## Acquisition rule

The GitHub connector can inspect and modify our repository but is not a substitute for a full Chromium checkout. Full upstream source acquisition/build must happen in a Windows build environment with sufficient disk, network and toolchain support. Until then, store integration manifests, adapters, patches and provenance—not a fake Chromium source tree.

## Research sources

- https://github.com/browseros-ai/BrowserOS
- https://github.com/open-browser-use/open-browser-use
- https://github.com/browser-use/browser-use
- https://github.com/AutoHotkey/AutoHotkey
- https://github.com/paradyno/PDF-MCP-Server
- https://github.com/nfsarch33/pdf-mcp-server
- https://github.com/ahamSel/WebPilot
