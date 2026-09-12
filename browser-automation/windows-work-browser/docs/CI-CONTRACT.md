# Windows Work Browser — CI Contract

## Purpose

This contract separates repository validation from the real Chromium/BrowserOS Windows build. A green lightweight CI job MUST NOT be interpreted as a compiled browser release.

## Required checks

### Contract CI (safe to run on normal hosted runners)

- validate required project directories and manifests
- validate TypeScript action contract syntax when toolchain is available
- validate documentation/provenance files are present
- fail if build status claims `COMPILED` without evidence metadata
- fail if an upstream is referenced without a pin/provenance record

### Windows browser build (dedicated runner)

A dedicated Windows x64 runner with the Chromium toolchain must:

1. checkout the exact project revision
2. acquire the pinned Chromium/BrowserOS source revision
3. verify source revision and patch set
4. sync dependencies
5. compile the browser
6. package the Windows artifact
7. launch the produced executable
8. execute navigation/tabs/profile/download/browser-control smoke tests
9. upload logs, hashes and artifact metadata

## Release gate

`COMPILED` is allowed only when all Windows build checks above pass and a real executable/package plus logs are retained. Documentation-only or contract-CI success must remain `NOT COMPILED YET`.

## Security gate

CI must also check that:

- model actions pass through the typed action contract and policy validator
- destructive/sensitive capabilities require approval according to policy
- arbitrary model-generated shell/AHK is not an execution primitive
- credentials are never stored in repository source
