# Windows Chromium Build Bootstrap

## Purpose

Define the reproducible machine contract required to build the Windows Work Browser. This is an execution recipe, not a claim that the build has already run.

## Host requirements

- Windows 11 x64 build machine
- Large SSD workspace (Chromium/BrowserOS builds can require very large working storage)
- Reliable network access to the pinned upstream source and dependencies
- Git
- Visual Studio 2022 with the required C++ desktop/toolchain components
- Windows SDK matching the selected Chromium revision
- Python and Chromium depot_tools required by the selected revision
- Sufficient RAM/CPU for Chromium compilation

## Bootstrap sequence

1. Record the exact BrowserOS and Chromium revisions in `docs/UPSTREAM-LOCK.md`.
2. Acquire the complete upstream checkout in the Windows build environment.
3. Install/configure `depot_tools` and the toolchain required by the pinned Chromium revision.
4. Sync dependencies using the upstream-recommended mechanism.
5. Apply only reviewed local patches.
6. Generate a Windows release configuration.
7. Compile the browser.
8. Produce a versioned executable/package.
9. Launch it on Windows.
10. Run browser smoke tests: startup, navigation, tabs, new window, profile, download and extension loading.
11. Retain build logs, test results, revision identifiers and artifact hashes.

## Build gate

The build is **PASS** only if the compiler exits successfully and a real Windows artifact exists. A green documentation/metadata CI job is not sufficient.

## Security gate

Secrets must not be embedded in source, build scripts, artifacts, logs or test fixtures. Signing credentials remain outside the repository and are injected only by the release environment.

## Expected evidence

- upstream revision(s)
- local patch list
- build command/configuration
- compiler result
- artifact filename and SHA-256
- Windows launch result
- smoke-test result
- CI/run URL or retained machine log
