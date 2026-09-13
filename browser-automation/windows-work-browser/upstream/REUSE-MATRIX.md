# Upstream Reuse Matrix

This project reuses upstream work as auditable components. Do not blindly merge unrelated repositories.

| Component | Upstream | Role | Integration form | License gate |
|---|---|---|---|---|
| Chromium/browser foundation | `browseros-ai/BrowserOS` | Full Chrome-class Windows browser | pinned source/base + local patches | AGPL-3.0 obligations |
| Browser control | `open-browser-use/open-browser-use` | Existing signed-in browser control, extension/native bridge, MCP | adapter/retained component | MIT |
| Agent reference | `browser-use/browser-use` | Agent patterns, Playwright automation, extraction | selective implementation/reference | MIT |
| Web automation | Microsoft Playwright | DOM, navigation, downloads, verification | dependency/adapter | upstream license review |
| Windows desktop | `AutoHotkey/AutoHotkey` | native dialogs, keyboard/mouse/window automation | controlled executor | upstream license review |
| UI reference | `lencx/Noi` | workspace/UI ideas only unless files are separately approved | reference | license audit required |

## Rules

- Preserve upstream notices and license files.
- Record immutable revision before vendoring or mirroring source.
- Prefer adapters over duplicate forks where practical.
- Never expose arbitrary shell/AHK/Playwright execution directly to an AI model.
- All actions pass through the product action contract and policy validator.
- Every release produces a dependency/license/SBOM report.
- If an upstream license is incompatible with the intended distribution model, replace it with an independently implemented interface rather than silently copying code.
