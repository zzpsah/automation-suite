# Windows Build Lanes

We use two legitimate lanes so product work is not blocked by Chromium's large native build.

## Lane A — Fast product integration

Purpose: get the Work Browser agent/control layer running against an already-built compatible BrowserOS/Chromium binary.

Inputs:
- a Windows x64 BrowserOS build supplied by an approved upstream release/build machine
- pinned BrowserOS source revision from `upstream/BROWSEROS-PIN.md`
- pinned open-browser-use revision
- this repository's agent contracts and adapters

Checks:
1. verify upstream artifact SHA-256;
2. verify browser version/provenance manifest;
3. install the product agent/native companion;
4. run Playwright/CDP/native bridge smoke tests;
5. produce an evidence bundle.

This lane is a product-integration build, **not** a Chromium source build.

## Lane B — Full Chromium build

Purpose: produce our own BrowserOS/Chromium executable from source.

Requirements:
- Windows build host with Visual Studio Build Tools;
- ~100GB free disk;
- 16GB+ RAM recommended;
- Python 3.12+ and `uv`;
- Chromium `depot_tools` checkout;
- network access to the pinned upstream sources.

The BrowserOS upstream contribution guide documents this native build as a separate, multi-hour path. Our bootstrap script pins the exact revisions before the build starts.

## Current environment workaround

The ChatGPT integration environment cannot host a 100GB Chromium checkout or execute a Windows toolchain. Therefore we do not fake a compiled result. The repository contains reproducible Windows bootstrap/build gates and can be executed on a self-hosted Windows runner or a dedicated Windows build VM.

**Recommended path:** Lane A first for usable product integration, then Lane B for the signed/reproducible release build.
