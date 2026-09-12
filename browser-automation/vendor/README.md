# Vendor / Reusable Upstream Components

This directory is reserved for upstream components that are intentionally retained for reuse.

## Policy
- Never copy an upstream repository without preserving its LICENSE/NOTICE and provenance.
- Prefer pinned git submodules, package dependencies, or a clearly documented source snapshot when technically appropriate.
- Every vendored component must appear in `../docs/UPSTREAM-COMPONENTS.md`.
- Store local patches separately and document why each patch exists.
- Keep the open-browser-use Chromium MV3 extension/native-host source available as a reusable component when its upstream license and Windows compatibility permit it.
- Do not silently fork or modify upstream behavior without recording the delta.

## Planned reusable modules
- `open-browser-use-extension/` — MV3 extension and native-host integration (to be imported/pinned after exact upstream revision and Windows support are verified).
- `browseros/` — Chromium/agent integration strategy; exact source strategy to be selected after build/licensing audit.
- `browser-use/` — agent automation reference/integration.
- `noi/` — UI/workspace reference.
- `autohotkey/` — Windows desktop automation adapter/reference.

The actual upstream source is not duplicated here until the repository's license, size, build requirements, and update strategy have been checked. This prevents an unmaintainable copy-and-paste vendor tree.
