# BrowserOS Upstream Pin

Purpose: record the exact upstream browser-control foundations selected for Windows Work Browser.

## BrowserOS

Repository: `browseros-ai/BrowserOS`
Branch: `main` (reference only; builds must use an immutable revision)

### Chromium pin

Source of truth in upstream:
`packages/browseros/CHROMIUM_VERSION`

Pinned Chromium version at integration time:
- MAJOR=151
- MINOR=0
- BUILD=7922
- PATCH=137

Source file SHA: `590b4197f4eb762762038a3600f57c484ddceaaa`

### BrowserOS Chromium base commit

Source of truth in upstream:
`packages/browseros/BASE_COMMIT`

Pinned base commit:
`8f5d36bc16f57115aeeff34baf4ad6aa964d509c`

## open-browser-use

Repository: `open-browser-use/open-browser-use`
Pinned revision: `7765002ac88040aedc781be89afe68475a9d6c88`
Release: `0.1.12`
License: MIT

## Integration rule

Do not copy an unpinned moving branch into the product. Every upstream materialization must record:

1. Repository URL.
2. Exact release/tag/revision.
3. License and notices.
4. Local patch stack.
5. Third-party dependency revisions.
6. SBOM/license manifest.
7. Build toolchain versions.
8. Produced artifact SHA-256.

This file is provenance evidence. It does not claim that a source build has been produced from the Chromium pin.
