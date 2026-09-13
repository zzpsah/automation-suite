# Upstream Components & Reuse Registry

This registry is the durable map for future DevOS work. DevOS should treat this document as the starting point when another project needs browser automation, MCP browser control, Chromium integration, or Windows desktop automation.

## BrowserOS
- Repository: https://github.com/browseros-ai/BrowserOS
- Role: primary Chromium/agent-browser architecture candidate.
- Relevant areas: Chromium fork/build system; agent platform; MCP/JSON APIs; CLI; browser extension/app.
- Current upstream licensing must be re-checked before redistribution or publishing a derivative.
- Reuse rule: prefer a pinned fork/patch series or vendored integration over copying files ad hoc.

## open-browser-use
- Repository: https://github.com/open-browser-use/open-browser-use
- License: MIT (verify current upstream LICENSE before each release).
- Role: real signed-in browser control, MV3 extension, native messaging, MCP server, Playwright-shaped TypeScript SDK, browser-control protocol.
- Current upstream architecture includes `packages/extension`, `packages/sdk`, `packages/browser-control-core`, `crates/obu-host`, `crates/obu-node-repl`, and `crates/obu-wire`.
- Important: preserve the extension and native-host implementation in the reusable source map. It must remain available for future projects instead of being treated as throwaway integration code.
- Windows status must be verified against the current upstream branch/release before enabling it as the default backend.

## browser-use
- Repository: https://github.com/browser-use/browser-use
- Role: agentic browser automation, MCP integration, extraction and workflow patterns.
- Reuse rule: use as an architecture/reference dependency only unless a specific package is deliberately adopted and its license is verified.

## Noi
- Repository: https://github.com/lencx/Noi
- Role: UI/workspace, local-first browser workflow and multi-window ideas.
- Reuse rule: inspect architecture and license before copying code.

## AutoHotkey
- Repository: https://github.com/AutoHotkey/AutoHotkey
- Role: Windows desktop automation backend.
- Reuse rule: invoke through a constrained adapter/action schema; never pass arbitrary model-generated scripts directly to the OS.

## Provenance requirements
For every adopted upstream component record:
1. upstream repository URL;
2. exact commit/tag/version;
3. license and required notices;
4. files/packages adopted;
5. local patches;
6. build instructions;
7. security review notes;
8. upgrade/diff procedure;
9. compatibility status on Windows;
10. test evidence.

## DevOS handoff contract
DevOS is the governing memory/orchestration layer. It should know:
- what upstream projects exist;
- where each component is stored;
- what each component does;
- exact pinned revisions;
- license obligations;
- integration boundaries;
- known Windows limitations;
- how to rebuild and test;
- which components are safe to reuse in future projects.

The browser project itself remains under `automation-suite/browser-automation`; DevOS governs the contract and memory, not the product's source tree.
