# BrowserOS Upstream Pin

Purpose: record the exact BrowserOS/Chromium base selected for Windows Work Browser.

## BrowserOS

Repository: `browseros-ai/BrowserOS`
Branch: `main` (reference only; builds must use an immutable revision)

## Chromium pin

Source of truth in upstream:
`packages/browseros/CHROMIUM_VERSION`

Pinned Chromium version at integration time:
- MAJOR=151
- MINOR=0
- BUILD=7922
- PATCH=137

Source file SHA: `590b4197f4eb762762038a3600f57c484ddceaaa`

## BrowserOS Chromium base commit

Source of truth in upstream:
`packages/browseros/BASE_COMMIT`

Pinned base commit:
`8f5d36bc16f57115aeeff34baf4ad6aa964d509c`

Source file SHA: `9c6e4174356d4ab4f5328cc4bd4747f1fa617aa5`

## Integration rule

Do not copy an unpinned moving `main` tree into the product. The Windows build lane must materialize the pinned revision and record:

1. BrowserOS source revision.
2. Chromium base commit.
3. Local patch stack revision.
4. Third-party component revisions.
5. License/SBOM manifest.
6. Build toolchain versions.
7. Produced artifact SHA-256.

This file is provenance evidence, not a claim that the Chromium source or Windows executable has already been built.
